# QA Checklist Template

## Pre-Release QA Checklist for StockLighthouse

**PR Number:** ___________  
**Reviewer:** ___________  
**Date:** ___________

---

## 🧪 Automated Tests

### Backend Tests
- [ ] All pytest tests pass (`cd backend && PYTHONPATH=src pytest tests/ -v`)
- [ ] Test coverage meets requirements (>80%)
- [ ] No new test failures introduced
- [ ] All test files follow naming convention (`test_*.py`)

**Command to run:**
```bash
cd backend
PYTHONPATH=src pytest tests/ -v --cov=stocklighthouse --cov-report=html
```

**Expected Result:** All tests pass with no failures or errors

---

### Frontend E2E Tests
- [ ] All Playwright tests pass (`cd frontend && npm run e2e`)
- [ ] Screenshots generated successfully
- [ ] No console errors in browser
- [ ] Tests run in under 5 minutes

**Command to run:**
```bash
cd frontend
npm run e2e
```

**Expected Result:** All E2E tests pass successfully

---

### Visual Regression Tests
- [ ] Visual diffs generated for changed pages
- [ ] All visual diffs reviewed and approved
- [ ] No unintended visual changes detected
- [ ] Baselines updated if changes are intentional

**Command to run:**
```bash
# After running E2E tests
node tests/utils/visual-diff.js tests/baseline frontend/.test-results/screenshots tests/diff 0.1
```

**Expected Result:** Visual differences < 10% or approved changes

---

## 🔧 Manual Testing

### Backend API
- [ ] API server starts without errors
- [ ] All endpoints respond with 200 OK
- [ ] Data normalization works correctly
- [ ] Error handling works as expected
- [ ] Cache functionality operates properly

**Commands:**
```bash
cd backend
PYTHONPATH=src uvicorn stocklighthouse.api.main:app --reload --port 8000
# In another terminal:
curl http://localhost:8000/health
```

---

### Frontend Application

#### Home Page
- [ ] Page loads without errors
- [ ] Search bar is functional
- [ ] Stock cards display correctly
- [ ] Clicking stock card navigates to detail page
- [ ] Navigation links work
- [ ] Responsive design works on mobile/tablet

#### Sector Dashboard
- [ ] Dashboard loads with sector tiles
- [ ] Heatmap displays with correct colors
- [ ] Statistics cards show accurate data
- [ ] Legend is visible and correct
- [ ] Back button navigates to home
- [ ] Sector tiles are clickable

#### Stock Detail Page
- [ ] Stock data loads correctly
- [ ] KPI table displays all metrics
- [ ] Price history chart renders
- [ ] PE distribution chart renders
- [ ] Charts are interactive (hover, zoom)
- [ ] Back navigation works
- [ ] Sector navigation works (if available)

**Commands:**
```bash
cd frontend
npm run dev
# Open http://localhost:5173 in browser
```

---

## 📊 Artifacts to Inspect

### Screenshots
- [ ] Review all generated screenshots in `frontend/.test-results/screenshots/`
- [ ] Verify UI elements are rendering correctly
- [ ] Check for visual regressions or unexpected changes

**Location:** `frontend/.test-results/screenshots/`

### Test Reports
- [ ] Review HTML test report: `frontend/playwright-report/index.html`
- [ ] Check backend test coverage report: `backend/htmlcov/index.html`
- [ ] Review any failed test logs

**Locations:**
- Frontend: `frontend/playwright-report/`
- Backend: `backend/htmlcov/`

### Visual Diffs
- [ ] Review diff images in `tests/diff/`
- [ ] Verify highlighted changes are intentional
- [ ] Document any approved visual changes

**Location:** `tests/diff/`

---

## 🐛 Bug Verification

### Regression Testing
- [ ] Previous bugs are still fixed
- [ ] No new bugs introduced
- [ ] Edge cases handled properly

### Known Issues
- [ ] List any known issues that are not blocking:

```
1. 
2. 
3. 
```

---

## 🔒 Security Checks

- [ ] No sensitive data exposed in logs
- [ ] API endpoints properly secured
- [ ] Input validation working correctly
- [ ] No XSS vulnerabilities in frontend
- [ ] Dependencies up to date with no critical vulnerabilities

**Commands:**
```bash
# Check for known vulnerabilities
cd frontend && npm audit
cd backend && pip check
```

---

## 📝 Documentation

- [ ] README is up to date
- [ ] API documentation is accurate
- [ ] Test documentation is current
- [ ] CHANGELOG updated (if applicable)
- [ ] Comments in code are clear and helpful

---

## 🚀 Deployment Readiness

- [ ] All CI/CD checks pass
- [ ] Build succeeds without warnings
- [ ] Environment variables documented
- [ ] Database migrations tested (if applicable)
- [ ] Rollback plan documented

---

## ✅ Final Sign-Off

### Test Summary
- **Total Tests Run:** ___________
- **Passed:** ___________
- **Failed:** ___________
- **Skipped:** ___________

### Issues Found
```
List any issues discovered during QA:

1. 
2. 
3. 
```

### Approval
- [ ] All critical issues resolved
- [ ] All tests passing
- [ ] Code review completed
- [ ] Ready for merge

**QA Reviewer Signature:** ___________  
**Date:** ___________

---

## 📚 Additional Resources

- [Testing Documentation](../README.md)
- [Backend Test Guide](../backend/tests/README.md)
- [E2E Test Guide](../frontend/e2e/README.md)
- [Visual Regression Guide](./VISUAL_REGRESSION.md)
