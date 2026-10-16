# AUDITRA — Renewable Energy Incident Intelligence & Forensic Investigation Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Validation-Pydantic%20v2-e92063.svg?style=flat&logo=pydantic)](https://docs.pydantic.dev/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61dafb.svg?style=flat&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/Typed-TypeScript%205-3178c6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Style-Tailwind%20CSS-38b2ac.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-pytest%2026%20passed-brightgreen.svg?style=flat)](backend/tests/)

> **FIX PS3 Hackathon Problem Statement**  
> *"The forecast was wrong. Was that predictable, controllable, or just bad luck?"*

---

## 1. Executive Summary

Ordinary SCADA systems and solar monitoring dashboards show alarms and percentage shortfalls after an underperformance event occurs. **AUDITRA** operates as an industrial **forensic investigation engine** for utility-scale solar assets.

AUDITRA reconstructs historical generation shortfalls through:
1. **Time-Locked Forensic Replay**: Enforces strict historical information boundaries (`available_at <= T`) to eliminate hindsight bias.
2. **Physical Generation Baseline**: Computes unconstrained physical expected power under verified plane-of-array irradiance and module temperature.
3. **Sequential Non-Overlapping Loss Attribution**: Eliminates double-counting across weather drops, grid curtailment, and inverter deratings with an explicit residual.
4. **Evidence-Tested Hypothesis Matrix**: Evaluates six competing physical hypotheses with transparent supporting, contradicting, and missing evidence.
5. **Bounded Preventability & Recoverable Energy**: Distinguishes between observed, detectable, actionable, and preventable losses under operational lag constraints.

---

## 2. Reference Asset: Helios-1 Solar Park

| Asset Parameter | Engineering Value | Notes |
| :--- | :--- | :--- |
| **Total AC Capacity** | **50.0 MW** | Inverter-clipped maximum export |
| **Inverter Blocks** | **4 Blocks (INV-01 .. INV-04)** | Modular architecture |
| **Block AC Capacity** | **12.5 MW each** | Symmetrical blocks |
| **Telemetry Interval** | **15 minutes (0.25 h)** | Standard utility settlement interval |
| **Physical Temperature Coeff ($\gamma$)** | **-0.004 / °C** | Relative to 25°C STC standard |
| **Standard Energy Semantics** | $\text{Energy [MWh]} = \text{AveragePower [MW]} \times 0.25\,\text{h}$ | Discrete interval average |

---

## 3. Four-Person Team Ownership & Module Boundaries

To ensure zero integration chaos and clear judging attribution, AUDITRA enforces strict file and module ownership:

```
AUDITRA/
├── README.md               [Heet Kakaria - Tech Lead]
├── CONTRIBUTING.md         [Heet Kakaria - Tech Lead]
├── .gitignore              [Heet Kakaria - Tech Lead]
├── .env.example            [Heet Kakaria - Tech Lead]
│
├── docs/                   [Heet Kakaria - Tech Lead]
│   ├── architecture.md
│   ├── api-contracts.md
│   ├── domain-model.md
│   ├── git-workflow.md
│   ├── rubric-mapping.md
│   ├── acceptance-tests.md
│   └── demo-guide.md
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         [Amulya Dongre - Backend Lead]
│   │   ├── schemas.py      [Heet Kakaria - Tech Lead]
│   │   ├── data/           [Amulya Dongre - Backend Lead]
│   │   ├── engine/         [Atharva Hoge - Domain Science Lead]
│   │   └── replay/         [Heet Kakaria - Tech Lead]
│   └── tests/
│       ├── test_api.py     [Amulya Dongre]
│       ├── test_data.py    [Amulya Dongre]
│       ├── test_engine.py  [Atharva Hoge]
│       └── test_replay.py  [Heet Kakaria]
│
└── frontend/               [Vedant Goyal - Frontend Lead]
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── types/
        ├── services/
        ├── components/
        └── pages/
```

### Team Roster:
- **Heet Kakaria (Tech Lead, Antigravity)**: Shared Pydantic contracts, historical replay orchestrator, temporal invariants, architecture, and cross-module integration.
- **Amulya Dongre (Backend & Data Pipeline)**: Deterministic synthetic scenario generation, delayed telemetry simulation, FastAPI endpoints, and data validation tests.
- **Atharva Hoge (Domain Science & Attribution Engine)**: Physical baseline calculations, sequential loss attribution waterfall, six competing hypotheses, and recoverable energy estimator.
- **Vedant Goyal (Frontend & Visualization)**: React control-room dashboard, flight-recorder timeline scrubber, evidence board, hypothesis matrix, and loss waterfall chart.

---

## 4. Physical Baseline & Loss Accounting Invariants

### Inverter Physical Baseline Model (Section 5):
$$P_{\text{phys},i} = \min\left(P_{\text{cap},i},\; \max\left(0,\; P_{\text{cap},i} \times \left(\frac{G_{\text{clean},i}}{1000}\right) \times (1 + \gamma \times (T_{\text{mod},i} - 25))\right)\right)$$

### Non-Overlapping Loss Attribution Waterfall (Section 6):
$$\text{Total Shortfall} = \text{Forecast Energy} - \text{Actual Energy}$$
$$\text{Total Shortfall} = \Delta E_{\text{weather}} + \Delta E_{\text{curtailment}} + \Delta E_{\text{equipment}} + \Delta E_{\text{other}} + \Delta E_{\text{residual}}$$

- **No Double Counting**: Sequential precedence ensures weather drops, grid dispatch caps, and inverter trips do not claim the same MWh.
- **Explicit Residual**: Any unaccounted difference is reported as `UNEXPLAINED_RESIDUAL` rather than hidden.
- **Bounded Preventability**: Observed loss $\neq$ preventable loss. Recovery estimates account for detection latency, communication lag, and cooling thermal inertia.

---

## 5. The Six Competing Hypotheses

| ID | Hypothesis Name | Supporting Telemetry Evidence |
| :--- | :--- | :--- |
| **H1** | **Equipment Derating** | Divergence across inverter blocks under equal POA, thermal alarms, status trip flags |
| **H2** | **Weather Drop** | Cross-sensor irradiance decrease tracking physical generation reduction |
| **H3** | **Grid Curtailment** | Transmission dispatch limit active; plant output clamped to dispatch order |
| **H4** | **Sensor Drift** | Disagreement between primary pyranometer and secondary reference sensor |
| **H5** | **Forecast Bias** | Systematic, persistent day-ahead prediction error under STC-comparable weather |
| **H6** | **Unexplained Residual** | Remaining shortfall after non-overlapping attribution |

---

## 6. Getting Started Locally

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run automated test suite
python -m pytest tests -v

# Start FastAPI local server
uvicorn app.main:app --reload --port 8000
```
Backend API interactive documentation is available at: `http://localhost:8000/docs`

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend control-room console is available at: `http://localhost:5173`

---

## 7. Rubric & Judging Strategy

For detailed mapping of hackathon judging criteria (50% Domain & Technical Depth) to modules and test suites, refer to [`docs/rubric-mapping.md`](docs/rubric-mapping.md).
