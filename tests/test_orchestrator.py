from __future__ import annotations

import json
from pathlib import Path

from experiment_matrix_orchestrator.orchestrator import OFFICIAL_FIELDS, RESEARCH_QUESTIONS, _check_scorer_key, _schema_matrix


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
    assert "preserve temporal and stimulus-response structure" in RESEARCH_QUESTIONS[1]["question"]
    assert "inspectable, reproducible, and clearly labeled mock" in RESEARCH_QUESTIONS[2]["question"]


def test_schema_matrix_has_matching_tsel_and_flat_pairs(tmp_path: Path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("x", encoding="utf-8")
    representations = {
        "gas_tsel_full_7": str(artifact),
        "gas_flat_full_7": str(artifact),
        "gas_tsel_reduced_no_context": str(artifact),
        "gas_flat_reduced_no_context": str(artifact),
        "gas_tsel_candidate_plus_assertion_basis": str(artifact),
        "gas_flat_candidate_plus_assertion_basis": str(artifact),
        "synapse_tsel_full_7": str(artifact),
        "synapse_flat_full_7": str(artifact),
        "synapse_tsel_reduced_no_context": str(artifact),
        "synapse_flat_reduced_no_context": str(artifact),
        "synapse_tsel_candidate_plus_assertion_basis": str(artifact),
        "synapse_flat_candidate_plus_assertion_basis": str(artifact),
    }

    matrix = _schema_matrix(representations)

    assert [row["rq_id"] for row in matrix["research_questions"]] == ["RQ1", "RQ2", "RQ3"]
    assert len(matrix["official_fields"]) == 7
    pairs = {}
    for condition in matrix["conditions"]:
        pairs.setdefault(condition["control_pair_id"], set()).add(condition["representation_kind"])
    assert all(kinds == {"tsel", "flat"} for kinds in pairs.values())


def test_public_example_matrix_is_valid_json():
    path = Path(__file__).resolve().parents[1] / "examples" / "experiment_matrix.example.json"

    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["domain"] == "olfaction"
    assert [row["rq_id"] for row in data["research_questions"]] == ["RQ1", "RQ2", "RQ3"]
    assert len(data["official_fields"]) == 7
