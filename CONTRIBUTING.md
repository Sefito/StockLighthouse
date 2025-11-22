Contributing to StockLighthouse

- Use the "Agent Task" issue template for any work assigned to an agent.
- Branch naming: agent/<agent-name>/<short-description>
- PRs should include:
  - Tests (pytest for backend, Playwright for UI)
  - "How to run locally" section in PR body
  - Screenshots for UI changes in `.test-results/screenshots/<issue-number>/`
- Labels:
  - agent-task
  - qa-needed
  - review-request
- For agent-run tasks, include the agent manifest ID and which agent handled the task.