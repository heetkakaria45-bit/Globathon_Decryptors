# AUDITRA — Judging Rubric & Feature Mapping

This document maps the FIX PS3 hackathon judging rubric to AUDITRA's codebase, module ownership, automated tests, and demonstration evidence.

The top 3 categories account for **50% of the total score**, driving our engineering focus on solar physics, deterministic replay, and evidence-tested forensic workflows.

---

## Rubric Matrix & Engineering Alignment

| Criterion | Weight | Engineering Objective | Relevant Modules | Automated Test Verification | Demonstration Evidence |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Domain Understanding** | **20%** | Correct solar PV physics, STC temperature coefficients, explicit engineering units, and non-overlapping sequential loss accounting | `backend/app/schemas.py`<br>`backend/app/engine/`<br>`docs/domain-model.md` | `test_engine.py` (STC baseline, capacity capping, derate factor, loss accounting identity) | Recharts loss waterfall chart; physical equation display; Helios-1 50 MW block metrics |
| **Technical Depth & Execution** | **15%** | Deterministic algorithms, UTC time-locked historical replay, zero data leakage, and rigorous Pydantic validation | `backend/app/replay/engine.py`<br>`backend/app/schemas.py` | `test_replay.py` (availability boundary, late-reported events, timezone equivalence, determinism) | Scrubbing the replay timeline excludes late-arriving maintenance logs and alarms |
| **Concept & Product Thinking** | **15%** | Differentiated forensic investigation platform answering *"Predictable, controllable, or bad luck?"* rather than generic SCADA alarms | `backend/app/engine/`<br>`docs/architecture.md`<br>`frontend/src/App.tsx` | `test_engine.py` (recovery estimate bounds, preventability modeling) | 6-Hypotheses evaluation board with supporting vs contradicting evidence tags |
| **Core Functionality** | **10%** | Functioning end-to-end incident investigation across synthetic scenarios with reproducible evidence | `backend/app/main.py`<br>`backend/app/data/`<br>`backend/app/replay/` | `test_api.py`<br>`test_data.py`<br>`test_replay.py` | Full scenario replay via `/api/replay` returning reconciled shortfall and recovery bounds |
| **UI/UX & Design** | **10%** | Professional dark industrial control-room aesthetic with high visual hierarchy, readable units, and timeline scrubbers | `frontend/` (Vedant Goyal)<br>`frontend/src/index.css`<br>`frontend/tailwind.config.js` | Frontend build validation (`npm run build`) | Real-time health indicator, scenario selector, flight recorder, and hypothesis matrix |
| **Presentation & Communication** | **10%** | Transparent, explainable outputs; explicit uncertainty (residuals never zeroed without evidence); reproducible demo | `docs/demo-guide.md`<br>`docs/api-contracts.md` | `test_engine.py` (explicit residual preservation) | Step-by-step judge walkthrough script demonstrating an identifiable inverter trip |
| **Teamwork & Collaboration** | **10%** | Strict module ownership, shared Pydantic contracts, branch protection, and zero integration chaos | `CONTRIBUTING.md`<br>`docs/git-workflow.md` | Multi-module test suite (28 passing tests across api, data, engine, and replay) | Modular Git commit history and clearly demarcated team boundaries |
| **Completeness** | **5%** | Complete, runnable, local-first deliverable with zero external AI API dependencies | Root workspace, `requirements.txt`, `package.json` | Full pytest run passing locally with zero errors | Fully executable local FastAPI server and React frontend |
| **Team Role** | **5%** | Clearly attributable individual contributions across all four team members | Team ownership roster in `README.md` and package headers | Dedicated test files (`test_replay.py`, `test_engine.py`, `test_api.py`, `test_data.py`) | Git commit log and documentation author attribution |

---

## Attribution & Role Accountability

- **Heet Kakaria (Tech Lead)**: Architectural integrity, shared Pydantic models (`backend/app/schemas.py`), time-locked replay engine (`backend/app/replay/engine.py`), replay acceptance tests (`test_replay.py`), and documentation suite.
- **Amulya Dongre (Backend Lead)**: FastAPI REST endpoints (`backend/app/main.py`), synthetic Helios-1 scenario generation (`backend/app/data/`), API contract and data tests (`test_api.py`, `test_data.py`).
- **Atharva Hoge (Domain Science Lead)**: Physical baseline model, sequential non-overlapping loss waterfall, 6 competing hypotheses, recoverable energy range, and domain engine tests (`test_engine.py`).
- **Vedant Goyal (Frontend Lead)**: React control console (`frontend/`), flight-recorder timeline scrubber, Recharts loss waterfall, evidence board, and frontend tests.
