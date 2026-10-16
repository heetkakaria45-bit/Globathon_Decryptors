# AUDITRA — Team Collaboration & Contribution Guidelines

This document governs team development, code ownership, pull requests, and contract stability for AUDITRA.

---

## 1. Team Ownership Boundaries

AUDITRA enforces strict file ownership to prevent merge conflicts and maintain integration discipline:

| Contributor | Role | Authorized Files & Directories | Primary Responsibilities |
| :--- | :--- | :--- | :--- |
| **Heet Kakaria** | Tech Lead | `README.md`, `CONTRIBUTING.md`, `.gitignore`, `docs/*`, `backend/app/schemas.py`, `backend/app/replay/*`, `backend/tests/test_replay.py` | Architecture, shared Pydantic contracts, historical replay orchestrator, release integration |
| **Amulya Dongre** | Backend Lead | `backend/app/main.py`, `backend/app/data/*`, `backend/tests/test_api.py`, `backend/tests/test_data.py` | Synthetic scenario generation, delayed telemetry simulation, FastAPI endpoints |
| **Atharva Hoge** | Domain Science Lead | `backend/app/engine/*`, `backend/tests/test_engine.py` | Physical baseline equations, non-overlapping loss waterfall, hypothesis evaluation, recovery estimator |
| **Vedant Goyal** | Frontend Lead | `frontend/*` | React control-room dashboard, flight-recorder scrubber, evidence board, loss visualization |

---

## 2. Core Integration Rules

1. **Shared Contract Stability (`backend/app/schemas.py`)**:
   - `schemas.py` is the single source of truth for all four contributors.
   - Any modification to `schemas.py` requires coordination with affected module owners before merging.
   - All frontend types in `frontend/src/types/schemas.ts` must mirror `backend/app/schemas.py`.

2. **Branching Model**:
   - `main` is protected and represents production-ready code.
   - Contributors work on dedicated feature branches:
     - `feat/schemas-validation` (Heet)
     - `feat/replay-orchestrator` (Heet)
     - `feat/scenario-generator` (Amulya)
     - `feat/api-endpoints` (Amulya)
     - `feat/domain-engine` (Atharva)
     - `feat/loss-waterfall` (Atharva)
     - `feat/incident-dashboard` (Vedant)
     - `feat/timeline-scrubber` (Vedant)

3. **Pull Request Acceptance Criteria**:
   - All tests in `backend/tests/` must pass (`pytest backend/tests`).
   - Frontend build must pass without TypeScript or Tailwind errors (`npm run build`).
   - No naive timestamps: all datetimes must be timezone-aware (UTC normalized).
   - No placeholder tests: tests must assert real physical invariants and validation rules.
   - No hardcoded secrets or arbitrary AI inference API calls.

4. **Commit Hygiene**:
   - Use conventional commit messages: `feat(...)`, `fix(...)`, `test(...)`, `docs(...)`.
   - Never force-push (`git push -f`) to `main`.
