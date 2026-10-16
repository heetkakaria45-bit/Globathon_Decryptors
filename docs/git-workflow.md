# AUDITRA Git & Collaboration Workflow

This document defines the Git conventions, branching strategy, code review protocols, and CI validation requirements for AUDITRA's four-person engineering team.

---

## 1. Branch Strategy & Ownership Mapping

```
main (protected integration branch)
  │
  ├── feat/shared-contracts     [Heet Kakaria]
  ├── feat/replay-orchestrator  [Heet Kakaria]
  ├── feat/scenario-generator   [Amulya Dongre]
  ├── feat/api-endpoints        [Amulya Dongre]
  ├── feat/loss-waterfall       [Atharva Hoge]
  ├── feat/hypotheses-matrix    [Atharva Hoge]
  └── feat/incident-dashboard   [Vedant Goyal]
```

### Strict File Ownership Matrix:
To eliminate merge conflicts, team members must only create or edit files within their assigned directories:

| Owner | Directory / Files |
| :--- | :--- |
| **Heet Kakaria (Tech Lead)** | `README.md`, `CONTRIBUTING.md`, `.gitignore`, `docs/*`, `backend/app/schemas.py`, `backend/app/replay/*`, `backend/tests/test_replay.py` |
| **Amulya Dongre (Backend Lead)** | `backend/app/main.py`, `backend/app/data/*`, `backend/tests/test_api.py`, `backend/tests/test_data.py` |
| **Atharva Hoge (Domain Lead)** | `backend/app/engine/*`, `backend/tests/test_engine.py` |
| **Vedant Goyal (Frontend Lead)**| `frontend/*` |

---

## 2. GitHub Branch Protection Setup

To safeguard the repository against accidental direct pushes or broken integration:

1. In GitHub, navigate to **Settings > Branches > Add branch protection rule**.
2. Set **Branch name pattern** to `main`.
3. Enable the following settings:
   - **Require a pull request before merging**.
   - **Require approvals**: At least 1 review (Tech Lead review required for schema changes).
   - **Require status checks to pass before merging**:
     - `pytest backend/tests`
   - **Do not allow bypassing the above settings**.

---

## 3. Pull Request Guidelines

Before opening a pull request into `main`:
1. **Sync with main**: Rebase or merge latest `main` into your feature branch:
   ```bash
   git checkout feat/<your-feature>
   git fetch origin
   git rebase origin/main
   ```
2. **Execute Local Verification**:
   ```bash
   # Run backend verification
   python -m pytest backend/tests -v
   ```
3. **Commit Conventions**:
   Use structured commit headers:
   - `feat(schemas): ...`
   - `feat(replay): ...`
   - `feat(data): ...`
   - `feat(engine): ...`
   - `feat(frontend): ...`
   - `test(replay): ...`
   - `docs(rubric): ...`

---

## 4. Contract Stability Protocol

If a team member discovers that a schema in `backend/app/schemas.py` requires an additional field or modified constraint:
1. Open an issue or communicate directly with Heet Kakaria (Tech Lead).
2. Never modify `schemas.py` directly without coordinating with Vedant (frontend type sync) and Atharva/Amulya (engine/data sync).
3. Update both `backend/app/schemas.py` and `frontend/src/types/schemas.ts` in the same coordinated merge.
