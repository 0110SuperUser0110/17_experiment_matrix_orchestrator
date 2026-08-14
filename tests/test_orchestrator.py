from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiment_matrix_orchestrator.orchestrator import (
    FIELD_ENVELOPES,
    OFFICIAL_FIELDS,
    PROJECTS,
    RESEARCH_QUESTIONS,
    _check_scorer_key,
    _render_flat,
    _schema_matrix,
)


def test_official_field_envelope_is_exactly_seven_fields():
    assert OFFICIAL_FIELDS == [
        "timestamp",
        "modality",
        "source",
        "signal_type",
        "value",
        "unit",
        "contextual_metadata",
    ]


def test_scorer_key_contract_requires_90_packets():
    payload = {"packets": [{"packet_id": f"packet_{index:04d}", "expected_status": "valid_encoding"} for index in range(90)]}

    _check_scorer_key(payload)


def test_all_three_approved_research_questions_are_present():
    assert [row["rq_id"] for row in RESEARCH_QUESTIONS] == ["RQ1", "RQ2", "RQ3"]
    assert "structural characteristics" in RESEARCH_QUESTIONS[0]["question"]
    assert RESEARCH_QUESTIONS[1]["question"] == "To what extent does TSEL preserve temporal and stimulus-response structure in generated mock olfactory data compared with flattened representations of the same data?"
    assert "inspectable, reproducible, and clearly labeled mock" in RESEARCH_QUESTIONS[2]["question"]


def test_schema_matrix_has_matching_tsel_and_flat_pairs(tmp_path: Path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("x", encoding="utf-8")
    representations = {}
    for case_id in ("packet_0001", "packet_0002"):
        for pattern_id, _fields, _scope in FIELD_ENVELOPES:
            representations[f"{case_id}__{pattern_id}__tsel"] = str(artifact)
            representations[f"{case_id}__{pattern_id}__flat"] = str(artifact)

    matrix = _schema_matrix(representations)

    assert [row["rq_id"] for row in matrix["research_questions"]] == ["RQ1", "RQ2", "RQ3"]
    assert len(matrix["official_fields"]) == 7
    assert matrix["one_event_per_representation"] is True
    assert len(matrix["conditions"]) == 2 * len(FIELD_ENVELOPES) * 2
    pairs = {}
    for condition in matrix["conditions"]:
        pairs.setdefault(condition["control_pair_id"], set()).add(condition["representation_kind"])
    assert all(kinds == {"tsel", "flat"} for kinds in pairs.values())


def test_all_independent_testing_repositories_are_checked():
    testing_projects = [path for path in PROJECTS.values() if path[:2].isdigit()]

    assert len(testing_projects) == 17


def test_strict_flat_is_atomic_and_rejects_event_streams():
    event = {
        "timestamp": "2026-01-01T09:04:08Z",
        "modality": "olfaction",
        "source": "mock_session_001",
        "signal_type": "neural_response",
        "value": 1.022631,
        "unit": "percent_signal_change",
        "contextual_metadata": {
            "temporal": {"start": "2026-01-01T09:04:08Z", "stream_id": "must-not-leak"},
            "completeness": {"missing_dimensions": ["odor_concentration"]},
        },
    }

    row = json.loads(_render_flat([event]))[0]

    assert row["time"] == event["timestamp"]
    assert row["missing_odor_concentration"] is True
    assert all(not isinstance(value, (dict, list)) for value in row.values())
    assert "contextual_metadata" not in row
    with pytest.raises(ValueError, match="exactly one event"):
        _render_flat([event, event])


def test_public_example_matrix_is_valid_json():
    path = Path(__file__).resolve().parents[1] / "examples" / "experiment_matrix.example.json"

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["domain"] == "olfaction"
    assert [row["rq_id"] for row in data["research_questions"]] == ["RQ1", "RQ2", "RQ3"]
    assert len(data["official_fields"]) == 7
