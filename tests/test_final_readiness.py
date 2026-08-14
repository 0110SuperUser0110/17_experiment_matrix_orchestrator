from __future__ import annotations

import hashlib
import json
from pathlib import Path

from experiment_matrix_orchestrator.final_readiness import (
    APPROVED_RESEARCH_QUESTIONS,
    _confirmatory_package_gates,
    _occupancy_gates,
)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exactly_three_approved_research_questions_are_frozen():
    assert len(APPROVED_RESEARCH_QUESTIONS) == 3
    assert APPROVED_RESEARCH_QUESTIONS[0].startswith("What structural characteristics")
    assert APPROVED_RESEARCH_QUESTIONS[2].endswith("before downstream computational modeling?")


def test_occupancy_gate_requires_complete_exhaustive_design(tmp_path: Path):
    package = tmp_path / "occupancy"
    evidence = package / "evidence.txt"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("public mock evidence", encoding="utf-8")
    _write_json(
        package / "artifact_manifest.json",
        {
            "event_count": 49,
            "condition_count": 25_088,
            "all_128_masks_per_event": True,
            "files": [{"path": "evidence.txt", "sha256": _hash(evidence)}],
        },
    )
    _write_json(package / "analysis/data_quality_report.json", {"all_checks_passed": True})
    _write_json(package / "analysis/analysis_summary.json", {"all_design_checks_passed": True})
    _write_json(package / "package/occupancy_manifest.json", {"all_seven_keys_retained": True, "conditions_per_event": 512})

    gates = _occupancy_gates(package)

    assert all(gate.passed for gate in gates)


def test_confirmatory_gate_requires_one_event_simultaneous_package(tmp_path: Path):
    package = tmp_path / "confirmatory"
    package.mkdir()
    manifest = {
        "one_event_per_prompt": True,
        "fresh_isolated_chat_per_prompt": True,
        "simultaneous_matched_pair_submission": True,
        "both_prompts_submitted_before_either_response_visible": True,
        "max_pair_submission_delta_ms": 1_000,
        "event_count": 6,
        "mask_count_per_event": 16,
        "pair_count_per_interface": 126,
        "prompt_count_per_interface": 252,
        "matched_pairs": [{}] * 126,
        "prompt_rows": [{}] * 252,
    }
    _write_json(package / "confirmatory_manifest.json", manifest)
    manifest_hash = _hash(package / "confirmatory_manifest.json")
    _write_json(
        package / "package_file_sha256.json",
        [{"path": "confirmatory_manifest.json", "sha256": manifest_hash}],
    )

    gates = _confirmatory_package_gates(package)

    assert all(gate.passed for gate in gates)
