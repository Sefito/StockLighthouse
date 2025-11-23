# Visual Regression Baseline Screenshots

This directory contains baseline screenshots used for visual regression testing.

## Purpose

These baseline images serve as the "golden" reference for visual regression tests. When tests run, current screenshots are compared against these baselines to detect unintended visual changes.

## Structure

Baseline screenshots are organized by page/component:

```
baseline/
├── home-page-full.png
├── home-page-hero.png
├── home-page-stock-list.png
├── sector-dashboard-full.png
├── sector-dashboard-stats.png
├── sector-dashboard-heatmap.png
├── sector-dashboard-legend.png
├── stock-detail-full.png
├── stock-detail-kpi.png
├── stock-detail-price-chart.png
└── stock-detail-pe-chart.png
```

## Usage

### Comparing Screenshots

Use the visual diff utility to compare current screenshots against baselines:

```bash
node tests/utils/visual-diff.js \
  tests/baseline \
  frontend/.test-results/screenshots \
  tests/diff \
  0.1
```

### Updating Baselines

When intentional UI changes are made:

1. Review the diff images to confirm changes are expected
2. Copy new screenshots to replace baselines:
   ```bash
   cp frontend/.test-results/screenshots/*.png tests/baseline/
   ```
3. Commit the updated baselines:
   ```bash
   git add tests/baseline/
   git commit -m "Update visual regression baselines for [feature/change]"
   ```

### Initial Setup

If this is a fresh repository without baselines:

1. Run E2E tests to generate screenshots:
   ```bash
   cd frontend
   npm run e2e
   ```
2. Copy generated screenshots to baseline:
   ```bash
   cp frontend/.test-results/screenshots/*.png tests/baseline/
   ```
3. Commit baselines:
   ```bash
   git add tests/baseline/
   git commit -m "Add initial visual regression baselines"
   ```

## CI/CD Integration

In CI/CD pipelines:
- Baseline screenshots are stored as artifacts in successful master branch builds
- Pull requests download baselines and compare against current test run
- Visual differences are reported in PR comments
- Diff images are uploaded as artifacts for review

## Maintenance

### When to Update

Update baselines when:
- ✅ Intentional UI changes (new design, layout changes)
- ✅ Component updates that change appearance
- ✅ CSS/styling modifications
- ✅ New features with visual elements

Do NOT update for:
- ❌ Unintended visual regressions
- ❌ Bugs that cause visual issues
- ❌ Environment-specific rendering differences

### Review Process

Before updating baselines:
1. Review all diff images
2. Verify changes are intentional
3. Get approval from design/product team
4. Document reason in commit message
5. Update this README if structure changes

## Troubleshooting

### Missing Baselines

If baselines are missing, tests will report warnings but won't fail. Generate baselines by running tests and copying screenshots.

### Outdated Baselines

If many tests fail with visual differences, baselines may be outdated. Review changes carefully before bulk updating.

### Large Diffs

If diffs exceed threshold despite identical appearance:
- Check for font rendering differences
- Verify viewport size consistency
- Review animation states
- Consider increasing threshold

## Related Documentation

- [Visual Regression Guide](./VISUAL_REGRESSION.md)
- [Testing Guide](./README.md)
- [QA Checklist](./QA_CHECKLIST.md)
