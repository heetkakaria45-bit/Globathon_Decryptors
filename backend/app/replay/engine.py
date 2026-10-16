"""
AUDITRA Time-Locked Forensic Replay Engine
Owner: Heet Kakaria (Tech Lead)

This module implements the core temporal replay invariant:
    available_at <= replay_time

It reconstructs what was knowable at historical instant T without hindsight bias.
Source data is never mutated. Repeated calls with identical inputs produce
strictly deterministic output.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Sequence, Tuple, List, Dict
from app.schemas import (
    TelemetryRecord,
    ForecastRecord,
    DispatchRecord,
    EvidenceRecord,
    ReplayContext,
    ensure_utc_datetime,
    EvidenceQuality
)


def filter_by_availability(
    records: Sequence[EvidenceRecord],
    replay_time: datetime
) -> Tuple[List[EvidenceRecord], List[EvidenceRecord]]:
    """
    Partition evidence records into eligible and excluded sets based on availability.

    Core Invariant:
        Eligible iff available_at <= replay_time (UTC).
    """
    t_replay = ensure_utc_datetime(replay_time)
    eligible: List[EvidenceRecord] = []
    excluded: List[EvidenceRecord] = []

    for r in records:
        if r.available_at <= t_replay:
            eligible.append(r)
        else:
            excluded.append(r)

    # Sort deterministically by event_time, then available_at, then evidence_id
    eligible.sort(key=lambda x: (x.event_time, x.available_at, x.evidence_id))
    excluded.sort(key=lambda x: (x.event_time, x.available_at, x.evidence_id))
    return eligible, excluded


def filter_telemetry_records(
    records: Sequence[TelemetryRecord],
    replay_time: datetime
) -> List[TelemetryRecord]:
    """
    Filter telemetry records available on or before replay_time.
    Deduplicates identical interval records and sorts chronologically.
    """
    t_replay = ensure_utc_datetime(replay_time)
    
    # Filter by available_at <= t_replay
    eligible = [r for r in records if r.available_at <= t_replay]
    
    # Deduplicate by (block_id, event_time) keeping latest available_at
    seen: Dict[Tuple[str, datetime], TelemetryRecord] = {}
    for r in eligible:
        key = (r.block_id, r.event_time)
        if key not in seen or r.available_at > seen[key].available_at:
            seen[key] = r

    result = list(seen.values())
    result.sort(key=lambda x: (x.event_time, x.block_id))
    return result


def filter_forecast_records(
    records: Sequence[ForecastRecord],
    replay_time: datetime
) -> List[ForecastRecord]:
    """
    Filter forecast records available on or before replay_time.
    If multiple revisions exist for the same target interval, retains the latest
    valid revision available prior to replay_time.
    """
    t_replay = ensure_utc_datetime(replay_time)
    eligible = [r for r in records if r.available_at <= t_replay]

    # Group by (block_id, event_time) picking latest available
    latest_revisions: Dict[Tuple[str, datetime], ForecastRecord] = {}
    for r in eligible:
        key = (r.block_id, r.event_time)
        if key not in latest_revisions or r.available_at > latest_revisions[key].available_at:
            latest_revisions[key] = r

    result = list(latest_revisions.values())
    result.sort(key=lambda x: (x.event_time, x.block_id))
    return result


def filter_dispatch_records(
    records: Sequence[DispatchRecord],
    replay_time: datetime
) -> List[DispatchRecord]:
    """
    Filter grid dispatch constraint records available on or before replay_time.
    Retains the latest active instruction for each interval.
    """
    t_replay = ensure_utc_datetime(replay_time)
    eligible = [r for r in records if r.available_at <= t_replay]

    latest_dispatches: Dict[datetime, DispatchRecord] = {}
    for r in eligible:
        if r.event_time not in latest_dispatches or r.available_at > latest_dispatches[r.event_time].available_at:
            latest_dispatches[r.event_time] = r

    result = list(latest_dispatches.values())
    result.sort(key=lambda x: x.event_time)
    return result


def audit_data_quality(
    telemetry: Sequence[TelemetryRecord],
    evidence: Sequence[EvidenceRecord]
) -> List[str]:
    """
    Perform forensic audit of data quality, flagging suspect readings,
    missing intervals, or degraded sensor provenance.
    """
    flags: List[str] = []

    # Check for degraded or suspect quality in evidence
    suspect_ev = [e.evidence_id for e in evidence if e.quality in (EvidenceQuality.SUSPECT, EvidenceQuality.DEGRADED)]
    if suspect_ev:
        flags.append(f"Contains {len(suspect_ev)} suspect/degraded evidence record(s): {', '.join(suspect_ev[:3])}")

    # Check for telemetry reporting delays exceeding 15 minutes
    delayed_telemetry = [
        t for t in telemetry
        if (t.available_at - t.event_time) > timedelta(minutes=15)
    ]
    if delayed_telemetry:
        flags.append(f"{len(delayed_telemetry)} interval telemetry record(s) experienced SCADA ingestion delay > 15m")

    # Check for inverter availability alarms
    derated_inverters = [t for t in telemetry if t.availability_ratio < 1.0 or t.active_alarms]
    if derated_inverters:
        blocks = sorted({t.block_id for t in derated_inverters})
        flags.append(f"Inverter operational anomalies or alarms detected on block(s): {', '.join(blocks)}")

    return flags


def build_replay_context(
    scenario_id: str,
    replay_time: datetime,
    telemetry: Sequence[TelemetryRecord],
    forecasts: Sequence[ForecastRecord],
    dispatches: Sequence[DispatchRecord],
    evidence: Sequence[EvidenceRecord]
) -> ReplayContext:
    """
    Construct the authoritative ReplayContext for the forensic engine.
    Applies the availability invariant across all input sources and audits data quality.
    """
    t_replay = ensure_utc_datetime(replay_time)

    eligible_ev, excluded_ev = filter_by_availability(evidence, t_replay)
    eligible_tel = filter_telemetry_records(telemetry, t_replay)
    eligible_fc = filter_forecast_records(forecasts, t_replay)
    eligible_disp = filter_dispatch_records(dispatches, t_replay)

    quality_flags = audit_data_quality(eligible_tel, eligible_ev)
    if excluded_ev:
        quality_flags.append(
            f"{len(excluded_ev)} late-arriving evidence item(s) quarantined from historical perspective"
        )

    return ReplayContext(
        scenario_id=scenario_id,
        replay_time=t_replay,
        eligible_telemetry=eligible_tel,
        eligible_forecasts=eligible_fc,
        eligible_dispatches=eligible_disp,
        eligible_evidence=eligible_ev,
        excluded_evidence=excluded_ev,
        data_quality_flags=quality_flags
    )
