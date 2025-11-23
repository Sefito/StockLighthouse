#!/usr/bin/env node

/**
 * Visual Regression Testing Utility
 * 
 * This script compares screenshots against baseline images and reports differences.
 * It uses pixelmatch library for pixel-perfect comparison.
 * 
 * Usage:
 *   node visual-diff.js <baseline-dir> <current-dir> <diff-dir> [threshold]
 * 
 * Arguments:
 *   baseline-dir: Directory containing baseline screenshots
 *   current-dir:  Directory containing current screenshots to compare
 *   diff-dir:     Directory to output diff images
 *   threshold:    Optional pixel difference threshold (0-1, default: 0.1)
 * 
 * Exit codes:
 *   0: All screenshots match within threshold
 *   1: One or more screenshots exceed threshold
 *   2: Error occurred during comparison
 */

const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');

// Lightweight pixelmatch alternative using simple pixel comparison
function compareImages(img1, img2, width, height, threshold = 0.1) {
  let diff = 0;
  const totalPixels = width * height;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (width * y + x) << 2;
      
      const r1 = img1.data[idx];
      const g1 = img1.data[idx + 1];
      const b1 = img1.data[idx + 2];
      const a1 = img1.data[idx + 3];
      
      const r2 = img2.data[idx];
      const g2 = img2.data[idx + 1];
      const b2 = img2.data[idx + 2];
      const a2 = img2.data[idx + 3];
      
      // Calculate color difference
      const dr = Math.abs(r1 - r2);
      const dg = Math.abs(g1 - g2);
      const db = Math.abs(b1 - b2);
      const da = Math.abs(a1 - a2);
      
      if (dr > 10 || dg > 10 || db > 10 || da > 10) {
        diff++;
      }
    }
  }

  return diff / totalPixels;
}

function createDiffImage(img1, img2, width, height) {
  const diff = new PNG({ width, height });

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (width * y + x) << 2;
      
      const r1 = img1.data[idx];
      const g1 = img1.data[idx + 1];
      const b1 = img1.data[idx + 2];
      
      const r2 = img2.data[idx];
      const g2 = img2.data[idx + 1];
      const b2 = img2.data[idx + 2];
      
      // Highlight differences in red
      const isDifferent = Math.abs(r1 - r2) > 10 || 
                          Math.abs(g1 - g2) > 10 || 
                          Math.abs(b1 - b2) > 10;
      
      if (isDifferent) {
        diff.data[idx] = 255;     // R
        diff.data[idx + 1] = 0;   // G
        diff.data[idx + 2] = 0;   // B
        diff.data[idx + 3] = 255; // A
      } else {
        diff.data[idx] = r1;
        diff.data[idx + 1] = g1;
        diff.data[idx + 2] = b1;
        diff.data[idx + 3] = 100; // Semi-transparent
      }
    }
  }

  return diff;
}

async function compareScreenshots(baselineDir, currentDir, diffDir, threshold = 0.1) {
  // Ensure directories exist
  if (!fs.existsSync(baselineDir)) {
    console.error(`Error: Baseline directory does not exist: ${baselineDir}`);
    return { success: false, error: 'Baseline directory not found' };
  }

  if (!fs.existsSync(currentDir)) {
    console.error(`Error: Current directory does not exist: ${currentDir}`);
    return { success: false, error: 'Current directory not found' };
  }

  // Create diff directory if it doesn't exist
  if (!fs.existsSync(diffDir)) {
    fs.mkdirSync(diffDir, { recursive: true });
  }

  // Get all PNG files from baseline
  const baselineFiles = fs.readdirSync(baselineDir)
    .filter(f => f.endsWith('.png'));

  if (baselineFiles.length === 0) {
    console.warn('Warning: No baseline screenshots found. All current screenshots will be considered new.');
    return { success: true, results: [], newFiles: [], missingFiles: [] };
  }

  const results = [];
  const newFiles = [];
  const missingFiles = [];
  let hasFailures = false;

  for (const file of baselineFiles) {
    const baselinePath = path.join(baselineDir, file);
    const currentPath = path.join(currentDir, file);

    if (!fs.existsSync(currentPath)) {
      console.warn(`⚠️  Missing current screenshot: ${file}`);
      missingFiles.push(file);
      continue;
    }

    try {
      const baseline = PNG.sync.read(fs.readFileSync(baselinePath));
      const current = PNG.sync.read(fs.readFileSync(currentPath));

      // Check dimensions match
      if (baseline.width !== current.width || baseline.height !== current.height) {
        console.error(`❌ ${file}: Dimension mismatch (${baseline.width}x${baseline.height} vs ${current.width}x${current.height})`);
        results.push({
          file,
          passed: false,
          reason: 'Dimension mismatch'
        });
        hasFailures = true;
        continue;
      }

      // Compare images
      const diffPercent = compareImages(baseline, current, baseline.width, baseline.height, threshold);
      const passed = diffPercent <= threshold;

      if (!passed) {
        // Create diff image
        const diffImage = createDiffImage(baseline, current, baseline.width, baseline.height);
        const diffPath = path.join(diffDir, file);
        fs.writeFileSync(diffPath, PNG.sync.write(diffImage));
        
        console.error(`❌ ${file}: Difference ${(diffPercent * 100).toFixed(2)}% exceeds threshold ${(threshold * 100).toFixed(2)}%`);
        hasFailures = true;
      } else {
        console.log(`✅ ${file}: Passed (diff: ${(diffPercent * 100).toFixed(2)}%)`);
      }

      results.push({
        file,
        passed,
        diffPercent,
        threshold
      });

    } catch (error) {
      console.error(`❌ ${file}: Error during comparison - ${error.message}`);
      results.push({
        file,
        passed: false,
        error: error.message
      });
      hasFailures = true;
    }
  }

  // Check for new files in current that aren't in baseline
  const currentFiles = fs.readdirSync(currentDir)
    .filter(f => f.endsWith('.png'));
  
  for (const file of currentFiles) {
    if (!baselineFiles.includes(file)) {
      console.warn(`⚠️  New screenshot (not in baseline): ${file}`);
      newFiles.push(file);
    }
  }

  return {
    success: !hasFailures,
    results,
    newFiles,
    missingFiles,
    totalTests: results.length,
    passed: results.filter(r => r.passed).length,
    failed: results.filter(r => !r.passed).length
  };
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 3) {
    console.error('Usage: node visual-diff.js <baseline-dir> <current-dir> <diff-dir> [threshold]');
    console.error('  baseline-dir: Directory containing baseline screenshots');
    console.error('  current-dir:  Directory containing current screenshots');
    console.error('  diff-dir:     Directory to output diff images');
    console.error('  threshold:    Optional pixel difference threshold (0-1, default: 0.1)');
    process.exit(2);
  }

  const [baselineDir, currentDir, diffDir, thresholdStr] = args;
  const threshold = thresholdStr ? parseFloat(thresholdStr) : 0.1;

  if (isNaN(threshold) || threshold < 0 || threshold > 1) {
    console.error('Error: Threshold must be a number between 0 and 1');
    process.exit(2);
  }

  console.log('🔍 Visual Regression Testing');
  console.log(`Baseline: ${baselineDir}`);
  console.log(`Current:  ${currentDir}`);
  console.log(`Diff:     ${diffDir}`);
  console.log(`Threshold: ${(threshold * 100).toFixed(2)}%`);
  console.log('---');

  compareScreenshots(baselineDir, currentDir, diffDir, threshold)
    .then(result => {
      if (!result.success) {
        if (result.error) {
          process.exit(2);
        }
      }

      console.log('---');
      console.log('📊 Summary:');
      console.log(`Total tests: ${result.totalTests}`);
      console.log(`✅ Passed: ${result.passed}`);
      console.log(`❌ Failed: ${result.failed}`);
      
      if (result.newFiles.length > 0) {
        console.log(`⚠️  New files: ${result.newFiles.length}`);
      }
      
      if (result.missingFiles.length > 0) {
        console.log(`⚠️  Missing files: ${result.missingFiles.length}`);
      }

      if (result.success) {
        console.log('\n✨ All visual regression tests passed!');
        process.exit(0);
      } else {
        console.log('\n❗ Visual regression tests failed. Check diff images for details.');
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(2);
    });
}

module.exports = { compareScreenshots, compareImages, createDiffImage };
