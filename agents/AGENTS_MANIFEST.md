# StockLighthouse — Agents Manifest and Guide

This file defines the custom agents we will use with Agent HQ to build StockLighthouse in a structured, testable way.

Overview
- Purpose: Split implementation into focused agents so you can assign tasks, collect artifacts (code, tests, screenshots), and validate automatically.
- Workflow: Create issues using the "Agent Task" template. Assign to a specific agent. Agents produce PRs or patch files, run tests, and upload artifacts (unit tests, e2e screenshots, coverage, build logs).

Agents (high level)
1. IngestorAgent
   - Role: Implement yfinance ingestor, batch fetching, rate-limiting, retries.
   - Output: ingest module, unit tests, integration demo.

2. NormalizerAgent
   - Role: Canonical KPI mapping, schema with pydantic models, edge-case handling.
   - Output: normalizer module, model definitions, property tests.

3. AnalyzerAgent
   - Role: Sector aggregation, derived metrics (median, weighted avg), performance.
   - Output: analyzer module, pandas-based aggregations, tests and sample outputs.

4. FrontendAgent
   - Role: React + TypeScript UI; communicates with FastAPI; builds charts and visual reports.
   - Output: React components, E2E tests that produce screenshots.

5. QAAgent
   - Role: Create unit & e2e tests, Playwright tests, visual regression baseline screenshots.
   - Output: tests/, screenshots/, step-by-step reproduction instructions.

6. DevOpsAgent
   - Role: CI, Dockerfile, deployment manifests, GitHub Actions that run tests + screenshot capture.
   - Output: CI workflows, Dockerfiles, infra notes.

7. DocsAgent
   - Role: Write onboarding docs, how-to-run, acceptance criteria, user guide for the UI and endpoints.
   - Output: README updates, API docs, sample requests/responses.

Agent constraints
- Keep changes modular per-agent in separate branches/PRs.
- Include tests for all new code (pytest for Python, Playwright for UI).
- Produce at least one screenshot per major UI view (search, stock detail, sector dashboard).
- Each agent must provide a "how to test locally" section in its PR description.

How to use
1. Create issues with the agent task template (see .github/ISSUE_TEMPLATE/agent_task.md).
2. Create agents in Agent HQ using the prompts in agents/prompts/.
3. Assign the issue to the corresponding agent and provide any extra context.
4. When agent finishes, review PR, run CI, and review screenshots in artifacts.

Acceptance
- Unit tests passing.
- Playwright screenshots captured and included in PR artifacts.
- Clear documentation (how to run tests, how to review screenshots).