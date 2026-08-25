from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


OCCUPANCY_RELATIVE = Path("08_schema_ablation/study_artifacts/field_occupancy_20260814")
HETEROGENEOUS_RELATIVE = Path(
    "18_approved_scope_heterogeneous_dataset_evaluator/study_artifacts/approved_scope_heterogeneous_20260825"
)
CONFIRMATORY_RELATIVE = Path(
    "15_multi_llm_representation_exposure_runner/study_packages/official_confirmatory_occupancy_v1"
)
COLLECTION_RELATIVE = Path("15_multi_llm_representation_exposure_runner/study_results/official_confirmatory_occupancy_v1")

APPROVED_RESEARCH_QUESTIONS = [
    "What structural characteristics are required to represent temporally dynamic sensory data within a unified encoding framework?",
    "To what extent does the proposed temporal encoding layer preserve temporal structure across heterogeneous datasets?",
]

REQUIRED_REPOSITORIES = {
    "TSEL": "ab45b47",
    "01_neutral_blind_evaluation_runner": "d9ca3f6",
    "02_private_answer_key_scorer": "f8a13ec",
    "05_flat_minimal_baseline": "ee3e29b",
    "06_flat_enriched_baseline": "debd670",
    "08_schema_ablation": "5121310",
    "09_rule_based_evaluator": "34075cd",
    "13_reproducibility_evidence_packager": "0f01ddf",
    "14_mock_generator_coordination": "f6ee330",
    "17_experiment_matrix_orchestrator": "df99de2",
    "18_approved_scope_heterogeneous_dataset_evaluator": "a705731",
}


@dataclass(frozen=True)
class FinalGate:
    name: str
    passed: bool
    detail: str
    phase: str

    def to_record(self) -> dict[str, Any]:
        return self.__dict__.copy()


def run_final_data_readiness(base: str | Path | None = None) -> dict[str, Any]:
    root = Path(base).resolve() if base else Path(__file__).resolve().parents[3]
    gates: list[FinalGate] = []
    gates.extend(_repository_gates(root))
    gates.extend(_occupancy_gates(root / OCCUPANCY_RELATIVE))
    gates.extend(_heterogeneous_gates(root / HETEROGENEOUS_RELATIVE))

    approved_study_ready = all(gate.passed for gate in gates if gate.phase == "approved-thesis")
    report = {
        "schema_version": "tsel-approved-thesis-readiness-v2",
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "research_questions": [
            {"rq_id": f"RQ{index}", "question": question}
            for index, question in enumerate(APPROVED_RESEARCH_QUESTIONS, start=1)
        ],
        "approved_study_ready": approved_study_ready,
        "collection_ready": approved_study_ready,
        "final_data_ready": approved_study_ready,
        "interpretation": {
            "approved_study_ready": "The evidence required by the two ARB-approved research questions is present and validated.",
            "publication_boundary": "External-system exposure, fields beyond seven, and a standalone reproducibility RQ do not gate the thesis.",
            "occupancy_boundary": "All seven named keys remain present; masks change populated values, not schema width.",
        },
        "gates": [gate.to_record() for gate in gates],
        "blockers": [gate.to_record() for gate in gates if not gate.passed],
    }
    output = Path(__file__).resolve().parents[2] / "reports" / "final_data_readiness.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _repository_gates(root: Path) -> list[FinalGate]:
    gates: list[FinalGate] = []
    for name, minimum_commit in REQUIRED_REPOSITORIES.items():
        repo = root / name
        if not (repo / ".git").exists():
            gates.append(FinalGate(f"repository-{name}", False, "independent Git repository missing", "approved-thesis"))
            continue
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", minimum_commit, "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        detail = f"required commit {minimum_commit} is {'present' if completed.returncode == 0 else 'absent'}"
        gates.append(FinalGate(f"repository-{name}", completed.returncode == 0, detail, "approved-thesis"))
    return gates


def _occupancy_gates(package: Path) -> list[FinalGate]:
    gates: list[FinalGate] = []
    try:
        artifact_manifest = _load_json(package / "artifact_manifest.json")
        quality = _load_json(package / "analysis" / "data_quality_report.json")
        analysis = _load_json(package / "analysis" / "analysis_summary.json")
        occupancy = _load_json(package / "package" / "occupancy_manifest.json")
        hashes_valid = _verify_manifest_hashes(package, artifact_manifest.get("files", []))
        design_valid = (
            artifact_manifest.get("event_count") == 49
            and artifact_manifest.get("condition_count") == 25_088
            and artifact_manifest.get("all_128_masks_per_event") is True
            and quality.get("all_checks_passed") is True
            and analysis.get("all_design_checks_passed") is True
            and occupancy.get("all_seven_keys_retained") is True
            and occupancy.get("conditions_per_event") == 512
        )
        detail = "49 events; 25,088 conditions; 128 masks in two lanes and two empty encodings"
        gates.append(FinalGate("occupancy-design", design_valid, detail, "approved-thesis"))
        gates.append(FinalGate("occupancy-artifact-hashes", hashes_valid, "artifact-manifest SHA-256 verification", "approved-thesis"))
    except Exception as exc:
        gates.append(FinalGate("occupancy-package", False, f"{type(exc).__name__}: {exc}", "approved-thesis"))
    return gates


def _heterogeneous_gates(package: Path) -> list[FinalGate]:
    gates: list[FinalGate] = []
    try:
        result = _load_json(package / "evaluation_results.json")
        artifact_manifest = _load_json(package / "artifact_manifest.json")
        questions = result.get("research_questions", [])
        criteria = result.get("approved_feasibility_criteria", {})
        design_valid = (
            [row.get("rq_id") for row in questions] == ["RQ1", "RQ2"]
            and [row.get("question") for row in questions] == APPROVED_RESEARCH_QUESTIONS
            and result.get("dataset_count") == 5
            and result.get("input_format_count") == 4
            and result.get("modality_count") == 4
            and result.get("total_event_count") == 27
            and result.get("all_approved_criteria_passed") is True
            and len(criteria) == 4
            and all(value is True for value in criteria.values())
            and all(row.get("all_checks_passed") is True for row in result.get("datasets", []))
        )
        hashes_valid = artifact_manifest.get("all_paths_relative") is True and _verify_manifest_hashes(
            package, artifact_manifest.get("files", [])
        )
        gates.append(
            FinalGate(
                "heterogeneous-approved-criteria",
                design_valid,
                "5 datasets; 4 input forms; 4 modalities; 27 events; all four approved criteria pass",
                "approved-thesis",
            )
        )
        gates.append(
            FinalGate(
                "heterogeneous-artifact-hashes",
                hashes_valid,
                "repository-relative artifact-manifest SHA-256 verification",
                "approved-thesis",
            )
        )
    except Exception as exc:
        gates.append(FinalGate("heterogeneous-package", False, f"{type(exc).__name__}: {exc}", "approved-thesis"))
    return gates


def _confirmatory_package_gates(package: Path) -> list[FinalGate]:
    gates: list[FinalGate] = []
    try:
        manifest = _load_json(package / "confirmatory_manifest.json")
        file_hashes = _load_json(package / "package_file_sha256.json")
        pairs = manifest.get("matched_pairs", [])
        prompts = manifest.get("prompt_rows", [])
        design_valid = (
            manifest.get("one_event_per_prompt") is True
            and manifest.get("fresh_isolated_chat_per_prompt") is True
            and manifest.get("simultaneous_matched_pair_submission") is True
            and manifest.get("both_prompts_submitted_before_either_response_visible") is True
            and manifest.get("max_pair_submission_delta_ms") == 1_000
            and manifest.get("event_count") == 6
            and manifest.get("mask_count_per_event") == 16
            and manifest.get("pair_count_per_interface") == 126
            and manifest.get("prompt_count_per_interface") == 252
            and len(pairs) == 126
            and len(prompts) == 252
        )
        hashes_valid = _verify_hash_index(package, file_hashes)
        gates.append(FinalGate("confirmatory-instrument", design_valid, "126 one-event matched pairs and 252 prompts per interface", "collection-readiness"))
        gates.append(FinalGate("confirmatory-package-hashes", hashes_valid, "frozen-package SHA-256 verification", "collection-readiness"))
    except Exception as exc:
        gates.append(FinalGate("confirmatory-package", False, f"{type(exc).__name__}: {exc}", "collection-readiness"))
    return gates


def _collection_gates(collection: Path) -> list[FinalGate]:
    if not collection.exists():
        return [FinalGate("public-interface-collection", False, "no public-interface result directory yet", "final-data")]
    try:
        manifest = _load_json(collection / "collection_manifest.json")
        planned_sites = manifest.get("planned_sites", [])
        completed_sites = manifest.get("completed_sites", [])
        responses = list(collection.glob("responses/**/*.json"))
        screenshots = list(collection.glob("screenshots/**/*.png"))
        logs = list(collection.glob("logs/**/*.json"))
        expected_pairs = int(manifest.get("expected_pairs_per_completed_site", 126)) * len(completed_sites)
        complete = (
            bool(planned_sites)
            and len(completed_sites) >= 4
            and int(manifest.get("completed_pair_count", 0)) == expected_pairs
            and len(responses) >= expected_pairs * 2
            and len(screenshots) >= expected_pairs * 4
            and len(logs) >= expected_pairs
            and manifest.get("all_delivery_tokens_valid") is True
            and manifest.get("all_pairs_within_submission_window") is True
            and manifest.get("all_pairs_one_event") is True
        )
        detail = f"{len(completed_sites)} completed sites; {len(responses)} responses; {len(screenshots)} screenshots"
        return [FinalGate("public-interface-collection", complete, detail, "final-data")]
    except Exception as exc:
        return [FinalGate("public-interface-collection", False, f"{type(exc).__name__}: {exc}", "final-data")]


def _verify_manifest_hashes(root: Path, rows: Any) -> bool:
    if not isinstance(rows, list) or not rows:
        return False
    for row in rows:
        if not isinstance(row, dict):
            return False
        path = root / str(row.get("path", ""))
        if not path.is_file() or _sha256(path) != row.get("sha256"):
            return False
    return True


def _verify_hash_index(root: Path, payload: Any) -> bool:
    if isinstance(payload, dict) and isinstance(payload.get("files"), list):
        rows = payload["files"]
    elif isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = [{"path": key, "sha256": value} for key, value in payload.items()]
    else:
        return False
    return _verify_manifest_hashes(root, rows)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
