"""
AUDITRA FastAPI Entrypoint
Owner: Amulya Dongre

This module sets up the FastAPI application, CORS middleware,
and exposes the primary API routes for AUDITRA.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas import ReplayRequest, ReplayResponse

app = FastAPI(
    title="AUDITRA API",
    description="Renewable-Energy Incident Intelligence & Forensic Investigation Platform",
    version="0.1.0",
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime


class ScenarioSummary(BaseModel):
    scenario_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    incident_category: str


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def get_health() -> HealthResponse:
    """System health check endpoint for monitoring and smoke tests."""
    return HealthResponse(
        status="healthy",
        service="AUDITRA-Backend",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc)
    )


@app.get("/api/scenarios", response_model=List[ScenarioSummary], tags=["Scenarios"])
def list_scenarios() -> List[ScenarioSummary]:
    """
    List available synthetic demonstration scenarios for Helios-1 Solar Park.
    Amulya will populate with realistic scenario telemetry data.
    """
    return [
        ScenarioSummary(
            scenario_id="SCENARIO-01-THERMAL-TRIP",
            title="Helios-1 Inverter Block 2 Overheating & Trip",
            description="High irradiance event causing INV-02 thermal alarm, delayed telemetry ingestion, and subsequent inverter shutdown.",
            start_time=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 6, 15, 16, 0, 0, tzinfo=timezone.utc),
            incident_category="Equipment Derating & Failure"
        ),
        ScenarioSummary(
            scenario_id="SCENARIO-02-GRID-CURTAILMENT-WEATHER",
            title="Overlapping Grid Curtailment & Cloud Transient",
            description="Grid operator dispatch cap active concurrently with sudden irradiance drop, demonstrating non-overlapping attribution.",
            start_time=datetime(2026, 7, 10, 11, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 7, 10, 15, 0, 0, tzinfo=timezone.utc),
            incident_category="Compound Curtailment & Weather"
        ),
        ScenarioSummary(
            scenario_id="SCENARIO-03-SENSOR-DRIFT",
            title="Primary Pyranometer Calibration Drift",
            description="Primary POA pyranometer degrades relative to secondary reference sensor, creating false forecast shortfall.",
            start_time=datetime(2026, 8, 5, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 5, 17, 0, 0, tzinfo=timezone.utc),
            incident_category="Instrumentation & Sensor Drift"
        )
    ]


@app.post("/api/replay", response_model=ReplayResponse, tags=["Forensics"])
def replay_investigation(request: ReplayRequest) -> ReplayResponse:
    """
    Time-locked forensic replay endpoint.
    Accepts scenario_id and timezone-aware replay_time.
    (Full integration orchestration will be completed in the next phase).
    """
    # Contract validation: request is automatically validated by Pydantic.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Replay execution engine will be wired in Phase 2 once scenario generation and attribution engines are implemented."
    )
