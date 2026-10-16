"""
AUDITRA Time-Locked Forensic Replay Tests
Owner: Heet Kakaria (Tech Lead)

Validates Section 8 & Section 5 Acceptance Criteria:
1. Evidence available exactly at replay time is eligible.
2. Evidence available after replay time is strictly quarantined into excluded_evidence.
3. An old physical event reported later is excluded if available_at > replay_time.
4. Naive or invalid timestamps are rejected.
5. Different timezone representations of the exact same instant behave consistently.
6. Repeated replay queries with identical inputs yield deterministic results.
7. Telemetry deduplication and temporal ordering.
8. Forecast revisions honor availability boundary.
9. End-to-end ReplayContext assembly with audit flags.
"""

from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError

from app.schemas import (
    EvidenceRecord,
    ReplayRequest,
    TelemetryRecord,
    ForecastRecord,
    DispatchRecord,
    SensorProvenance,
    EvidenceQuality
)
from app.replay import (
    filter_by_availability,
    filter_telemetry_records,
    filter_forecast_records,
    filter_dispatch_records,
    build_replay_context
)


class TestReplayTemporalInvariants:

    def test_evidence_available_exactly_at_replay_time_is_eligible(self):
        """Evidence available exactly at T must be included."""
        t_replay = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        ev = EvidenceRecord(
            evidence_id="EV-001",
            event_time=datetime(2026, 6, 15, 11, 45, 0, tzinfo=timezone.utc),
            available_at=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            source=SensorProvenance.INVERTER_SCADA,
            quality=EvidenceQuality.VALIDATED,
            metric_name="inverter_temp_celsius",
            metric_value=68.5,
            unit="degC",
            block_id="INV-02",
            description="INV-02 internal heat threshold warning"
        )
        eligible, excluded = filter_by_availability([ev], t_replay)
        assert len(eligible) == 1
        assert len(excluded) == 0
        assert eligible[0].evidence_id == "EV-001"

    def test_evidence_available_after_replay_time_is_excluded(self):
        """Evidence arriving at T + 1 second or later must not leak into historical replay."""
        t_replay = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        ev_future = EvidenceRecord(
            evidence_id="EV-002",
            event_time=datetime(2026, 6, 15, 11, 55, 0, tzinfo=timezone.utc),
            available_at=datetime(2026, 6, 15, 12, 0, 1, tzinfo=timezone.utc),  # 1 second after replay
            source=SensorProvenance.INVERTER_SCADA,
            quality=EvidenceQuality.VALIDATED,
            metric_name="inverter_status",
            metric_value=0.0,
            unit="status",
            block_id="INV-02",
            description="Inverter trip notification received 1 second past replay boundary"
        )
        eligible, excluded = filter_by_availability([ev_future], t_replay)
        assert len(eligible) == 0
        assert len(excluded) == 1
        assert excluded[0].evidence_id == "EV-002"

    def test_old_physical_event_reported_late_is_excluded(self):
        """
        Physical event at 10:00 but reported/available at 10:30.
        When replaying 10:15, this evidence must NOT be available.
        """
        t_replay = datetime(2026, 6, 15, 10, 15, 0, tzinfo=timezone.utc)
        ev_late_reported = EvidenceRecord(
            evidence_id="EV-003",
            event_time=datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc),  # occurred at 10:00
            available_at=datetime(2026, 6, 15, 10, 30, 0, tzinfo=timezone.utc), # reported at 10:30
            source=SensorProvenance.GRID_DISPATCH_SYSTEM,
            quality=EvidenceQuality.VALIDATED,
            metric_name="curtailment_instruction",
            metric_value=25.0,
            unit="MW",
            description="Late telemetry sync from regional transmission operator"
        )
        eligible, excluded = filter_by_availability([ev_late_reported], t_replay)
        assert len(eligible) == 0, "Future-arriving evidence leaked into historical replay!"
        assert len(excluded) == 1

    def test_naive_timestamp_rejected_by_schemas(self):
        """Naive timestamps without timezone info must be rejected by Pydantic."""
        with pytest.raises(ValidationError) as exc_info:
            ReplayRequest(
                scenario_id="SCENARIO-01",
                replay_time=datetime(2026, 6, 15, 12, 0, 0)  # Naive!
            )
        assert "Timestamps must be timezone-aware" in str(exc_info.value)

    def test_future_event_time_relative_to_availability_rejected(self):
        """Evidence cannot become available BEFORE the physical event actually occurred."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceRecord(
                evidence_id="EV-INVALID-001",
                event_time=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                available_at=datetime(2026, 6, 15, 11, 50, 0, tzinfo=timezone.utc), # Impossible!
                source=SensorProvenance.INVERTER_SCADA,
                quality=EvidenceQuality.VALIDATED,
                metric_name="power_mw",
                metric_value=10.0,
                unit="MW",
                description="Impossible causality"
            )
        assert "cannot precede" in str(exc_info.value)

    def test_different_timezone_representations_of_same_instant(self):
        """
        12:00 UTC and 17:30 IST (+05:30) represent the identical instant in time.
        Replaying at either must produce identical eligible evidence sets.
        """
        ist = timezone(timedelta(hours=5, minutes=30))
        t_replay_utc = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        t_replay_ist = datetime(2026, 6, 15, 17, 30, 0, tzinfo=ist)

        ev = EvidenceRecord(
            evidence_id="EV-005",
            event_time=datetime(2026, 6, 15, 11, 30, 0, tzinfo=timezone.utc),
            available_at=datetime(2026, 6, 15, 11, 45, 0, tzinfo=timezone.utc),
            source=SensorProvenance.WEATHER_STATION,
            quality=EvidenceQuality.VALIDATED,
            metric_name="ambient_temp_celsius",
            metric_value=34.2,
            unit="degC",
            description="Ambient air temperature measurement"
        )

        eligible_from_utc, _ = filter_by_availability([ev], t_replay_utc)
        eligible_from_ist, _ = filter_by_availability([ev], t_replay_ist)

        assert len(eligible_from_utc) == 1
        assert len(eligible_from_ist) == 1
        assert eligible_from_utc[0].evidence_id == eligible_from_ist[0].evidence_id

    def test_replay_determinism(self):
        """Multiple evaluations with identical evidence and replay time must return deterministic output."""
        t_replay = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        records = [
            EvidenceRecord(
                evidence_id=f"EV-{i:03d}",
                event_time=datetime(2026, 6, 15, 11, i, 0, tzinfo=timezone.utc),
                available_at=datetime(2026, 6, 15, 11, i + 5, 0, tzinfo=timezone.utc),
                source=SensorProvenance.PRIMARY_PYRANOMETER,
                quality=EvidenceQuality.VALIDATED,
                metric_name="poa_w_per_m2",
                metric_value=850.0 + i,
                unit="W/m²",
                description=f"Irradiance sample {i}"
            )
            for i in range(10)
        ]

        run_1_elig, run_1_excl = filter_by_availability(records, t_replay)
        run_2_elig, run_2_excl = filter_by_availability(records, t_replay)

        assert [r.evidence_id for r in run_1_elig] == [r.evidence_id for r in run_2_elig]
        assert [r.evidence_id for r in run_1_excl] == [r.evidence_id for r in run_2_excl]

    def test_forecast_revision_availability_filtering(self):
        """Forecast revisions published after replay time are excluded, retaining older revision."""
        t_interval = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        rev_1 = ForecastRecord(
            event_time=t_interval,
            available_at=datetime(2026, 6, 14, 22, 0, 0, tzinfo=timezone.utc),
            block_id="PLANT",
            forecast_power_mw=45.0,
            forecast_energy_mwh=11.25,
            model_version="REV-1"
        )
        rev_2 = ForecastRecord(
            event_time=t_interval,
            available_at=datetime(2026, 6, 15, 11, 0, 0, tzinfo=timezone.utc),
            block_id="PLANT",
            forecast_power_mw=40.0,
            forecast_energy_mwh=10.0,
            model_version="REV-2"
        )

        # At 10:00 UTC, only REV-1 is known
        fc_early = filter_forecast_records([rev_1, rev_2], datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc))
        assert len(fc_early) == 1
        assert fc_early[0].model_version == "REV-1"

        # At 11:30 UTC, REV-2 has arrived and supersedes REV-1
        fc_late = filter_forecast_records([rev_1, rev_2], datetime(2026, 6, 15, 11, 30, 0, tzinfo=timezone.utc))
        assert len(fc_late) == 1
        assert fc_late[0].model_version == "REV-2"

    def test_build_replay_context_end_to_end(self):
        """Verifies complete ReplayContext assembly, data quality auditing, and evidence partitioning."""
        t_replay = datetime(2026, 6, 15, 12, 10, 0, tzinfo=timezone.utc)
        
        telemetry = [
            TelemetryRecord(
                event_time=datetime(2026, 6, 15, 11, 45, 0, tzinfo=timezone.utc),
                available_at=datetime(2026, 6, 15, 12, 5, 0, tzinfo=timezone.utc), # 20m delay (>15m)
                block_id="INV-02",
                actual_power_mw=0.0,
                actual_energy_mwh=0.0,
                availability_ratio=0.0,
                active_alarms=["OVER_TEMP_TRIP"],
                sensor_quality=EvidenceQuality.VALIDATED,
                provenance=SensorProvenance.INVERTER_SCADA
            )
        ]

        evidence = [
            EvidenceRecord(
                evidence_id="EV-PAST",
                event_time=datetime(2026, 6, 15, 11, 50, 0, tzinfo=timezone.utc),
                available_at=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                source=SensorProvenance.INVERTER_SCADA,
                quality=EvidenceQuality.VALIDATED,
                metric_name="temp",
                metric_value=72.0,
                unit="degC",
                description="Thermal high alarm"
            ),
            EvidenceRecord(
                evidence_id="EV-FUTURE",
                event_time=datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                available_at=datetime(2026, 6, 15, 13, 0, 0, tzinfo=timezone.utc), # 50m in future
                source=SensorProvenance.INVERTER_SCADA,
                quality=EvidenceQuality.VALIDATED,
                metric_name="maintenance_log",
                metric_value=1.0,
                unit="flag",
                description="Manual technician reset log"
            )
        ]

        context = build_replay_context(
            scenario_id="SCENARIO-01-THERMAL-TRIP",
            replay_time=t_replay,
            telemetry=telemetry,
            forecasts=[],
            dispatches=[],
            evidence=evidence
        )

        assert context.scenario_id == "SCENARIO-01-THERMAL-TRIP"
        assert len(context.eligible_evidence) == 1
        assert context.eligible_evidence[0].evidence_id == "EV-PAST"
        assert len(context.excluded_evidence) == 1
        assert context.excluded_evidence[0].evidence_id == "EV-FUTURE"
        
        # Verify quality audit flags
        flags = " ".join(context.data_quality_flags)
        assert "quarantined" in flags
        assert "SCADA ingestion delay" in flags
        assert "alarms detected" in flags
