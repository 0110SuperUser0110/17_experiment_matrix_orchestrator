from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECTS = {
    "tsel": "TSEL",
    "neutral": "01_neutral_blind_evaluation_runner",
    "scorer": "02_private_answer_key_scorer",
    "timeline": "03_timeline_recovery_scorer",
    "missingness": "04_missingness_collection_quality_scorer",
    "flat_minimal": "05_flat_minimal_baseline",
    "flat_enriched": "06_flat_enriched_baseline",
    "time_series_baseline": "07_time_series_feature_baseline",
    "schema_ablation": "08_schema_ablation",
    "rule_based": "09_rule_based_evaluator",
    "classical_ml": "10_classical_ml_evaluator",
    "sequence": "11_sequence_time_series_evaluator",
    "token_model": "12_optional_token_model_evaluator",
    "repro": "13_reproducibility_evidence_packager",
    "mock_coordination": "14_mock_generator_coordination",
    "llm_exposure": "15_multi_llm_representation_exposure_runner",
    "schema_planner": "16_schema_field_envelope_comparison_planner",
    "orchestrator": "17_experiment_matrix_orchestrator",
    "heterogeneous": "18_approved_scope_heterogeneous_dataset_evaluator",
    "mock_generator": "olfactory mock Generator/mock-olfactory-generator",
}

OFFICIAL_FIELDS = [
    "timestamp",
    "modality",
    "source",
    "signal_type",
    "value",
    "unit",
    "contextual_metadata",
]

CANDIDATE_FIELDS = ["assertion_basis", "collection_quality"]

FIELD_ENVELOPES = [
    ("tsel_1_timestamp", OFFICIAL_FIELDS[:1], "thesis"),
    ("tsel_2_time_modality", OFFICIAL_FIELDS[:2], "thesis"),
    ("tsel_3_time_modality_source", OFFICIAL_FIELDS[:3], "thesis"),
    ("tsel_4_add_signal_type", OFFICIAL_FIELDS[:4], "thesis"),
    ("tsel_5_add_value", OFFICIAL_FIELDS[:5], "thesis"),
    ("tsel_6_add_unit", OFFICIAL_FIELDS[:6], "thesis"),
    ("tsel_7_full", OFFICIAL_FIELDS, "thesis"),
    ("tsel_8_add_assertion_basis", [*OFFICIAL_FIELDS, "assertion_basis"], "publication"),
    ("tsel_9_add_collection_quality", [*OFFICIAL_FIELDS, "assertion_basis", "collection_quality"], "publication"),
]

RESEARCH_QUESTIONS = [
    {
        "rq_id": "RQ1",
        "question": "What structural characteristics are required to represent temporally dynamic sensory data within a unified encoding framework?",
        "evidence_paths": ["schema_field_envelope_plan", "tsel_vs_flat_controls", "reduced_field_ablations"],
    },
    {
        "rq_id": "RQ2",
        "question": "To what extent does the proposed temporal encoding layer preserve temporal structure across heterogeneous datasets?",
        "evidence_paths": ["heterogeneous_dataset_evaluation", "neutral_blind_tsel_run", "timeline_recovery", "flattened_baselines"],
    },
]

QUALITY_CONTROLS = [
    {
        "control_id": "QC1",
        "name": "inspectability-reproducibility-and-mock-labeling",
        "research_question": False,
        "evidence_paths": ["mock_manifest_validation", "private_key_boundary", "reproducibility_evidence_packaging", "hash_records"],
    }
]

PUBLICATION_SCOPE = [
    "external computational-system representation exposure",
    "candidate fields beyond the approved seven-field envelope",
    "standalone reproducibility and inspectability research question",
]

QUESTION_SET = [
    {
        "question_id": "temporal_placement",
        "question": "For this one event, report observable timestamp or start, end, duration, resolution, uncertainty, event kind, and explicit temporal relations; mark unsupported items unresolved.",
    },
    {
        "question_id": "missingness_summary",
        "question": "For this one event, return missing or weakened evidence signals without inventing absent timing or stimulus facts.",
    },
    {
        "question_id": "stimulus_response_linkage",
        "question": "For this one event, report only explicit stimulus-response linkage and leave absent linkage unresolved.",
    },
    {
        "question_id": "simplicity_control",
        "question": "For this one event, distinguish atomic observed facts from structural temporal information without inferring absent facts.",
    },
    {
        "question_id": "temporal_reconstruction",
        "question": "Reconstruct this one event with its supported temporal fields and explicit unresolved fields.",
    },
]


@dataclass(frozen=True)
class PreparedArtifacts:
    base: str
    public_manifest: str
    neutral_manifest: str
    neutral_config: str
    scorer_answer_key: str
    schema_matrix: str
    schema_plan_output: str
    exposure_manifest: str
    free_llm_manifest: str
    evidence_manifest: str

    def to_record(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    detail: str
    blocking: bool = True

    def to_record(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "blocking": self.blocking, "detail": self.detail}


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    generated_at: str
    gates: list[Gate]
    warnings: list[str]
    prepared: PreparedArtifacts

    def to_record(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "generated_at": self.generated_at,
            "research_questions": RESEARCH_QUESTIONS,
            "warnings": self.warnings,
            "prepared": self.prepared.to_record(),
            "gates": [gate.to_record() for gate in self.gates],
        }


def prepare_artifacts(base: str | Path | None = None) -> PreparedArtifacts:
    paths = _paths(base)
    dataset = paths["mock_generator"] / "datasets" / "blind_olfactory_validation_001"
    neutral_actual_report = paths["neutral"] / "outputs" / "official_readiness" / "actual_run" / "neutral_run_report.json"

    public_manifest = paths["mock_coordination"] / "outputs" / "official_readiness" / "public_mock_manifest.json"
    neutral_manifest = paths["neutral"] / "outputs" / "official_readiness" / "public_packet_manifest.json"
    neutral_config = paths["neutral"] / "outputs" / "official_readiness" / "runner_config.dry_run.json"
    neutral_run_config = paths["neutral"] / "outputs" / "official_readiness" / "runner_config.actual.json"
    scorer_answer_key = paths["scorer"] / "private_answer_keys" / "official_status_key.local.json"
    schema_matrix = paths["schema_planner"] / "work" / "official" / "schema_field_matrix.json"
    schema_plan_output = paths["schema_planner"] / "outputs" / "official_schema_plan"
    exposure_manifest = paths["llm_exposure"] / "work" / "official" / "exposure_manifest.json"
    evidence_manifest = paths["repro"] / "work" / "official" / "evidence_manifest.json"

    _write_json(public_manifest, _public_mock_manifest(dataset))
    neutral_payload, pilot_payload = _neutral_packet_manifests(dataset)
    _write_json(neutral_manifest, neutral_payload)
    _write_json(neutral_manifest.parent / "pilot_public_packet_manifest.json", pilot_payload)
    _write_json(neutral_config, _neutral_runner_config(neutral_manifest, paths["tsel"], dry_run=True))
    _write_json(neutral_run_config, _neutral_runner_config(neutral_manifest, paths["tsel"], dry_run=False))
    _write_json(scorer_answer_key, _scorer_answer_key(dataset / "answer_key_private.json"))

    representation_dir = paths["llm_exposure"] / "work" / "official" / "representations"
    representations = _write_representations(neutral_actual_report, representation_dir)
    _write_json(schema_matrix, _schema_matrix(representations))
    _write_json(exposure_manifest, _exposure_manifest(representations))
    free_llm_manifest = paths["llm_exposure"] / "outputs" / "official_one_event_readiness" / "free_llm_packet_manifest.json"
    _write_json(evidence_manifest, _evidence_manifest(public_manifest, neutral_manifest, schema_matrix, exposure_manifest, neutral_actual_report))

    return PreparedArtifacts(
        base=str(_base(base)),
        public_manifest=str(public_manifest),
        neutral_manifest=str(neutral_manifest),
        neutral_config=str(neutral_config),
        scorer_answer_key=str(scorer_answer_key),
        schema_matrix=str(schema_matrix),
        schema_plan_output=str(schema_plan_output),
        exposure_manifest=str(exposure_manifest),
        free_llm_manifest=str(free_llm_manifest),
        evidence_manifest=str(evidence_manifest),
    )


def run_readiness(base: str | Path | None = None) -> ReadinessReport:
    prepared = prepare_artifacts(base)
    paths = _paths(base)
    gates: list[Gate] = []
    warnings: list[str] = []

    gates.extend(_check_repositories(paths))
    gates.append(_run_command_gate("testing-project-suite", _suite_command(_base(base)), _base(base), timeout=180))
    gates.append(_run_command_gate("tsel-focused-tests", [sys.executable, "-m", "pytest", "-q", "tests/test_exports.py", "tests/test_supported_recovery.py", "tests/test_standard.py", "tests/test_pipeline.py"], paths["tsel"], timeout=120))
    gates.append(_run_command_gate("mock-generator-validation", [sys.executable, "-m", "mock_olfactory_generator", "validate-blind-dataset", "--input", "datasets/blind_olfactory_validation_001", "--source-profile", "source_profiles/human_olfaction_composite_profile.json"], paths["mock_generator"], timeout=180, pythonpath="src"))
    gates.append(_run_command_gate("public-mock-manifest", [sys.executable, "-m", "mock_generator_coordination.cli", prepared.public_manifest, str(paths["mock_coordination"] / "outputs" / "official_readiness" / "public_manifest.report.json")], paths["mock_coordination"], timeout=60, pythonpath="src"))
    gates.append(_run_command_gate("neutral-blind-dry-run", [sys.executable, "-m", "neutral_blind_runner.cli", "--config", prepared.neutral_config], paths["neutral"], timeout=120, pythonpath="src"))
    neutral_actual_config = paths["neutral"] / "outputs" / "official_readiness" / "runner_config.actual.json"
    gates.append(_run_neutral_official(paths, neutral_actual_config))
    if gates[-1].passed:
        prepared = prepare_artifacts(base)
    gates.append(_check_json_gate("scorer-answer-key-contract", Path(prepared.scorer_answer_key), _check_scorer_key))
    gates.append(
        _run_command_gate(
            "official-private-scorer",
            [
                sys.executable,
                "-m",
                "private_answer_key_scorer.cli",
                str(paths["neutral"] / "outputs" / "official_readiness" / "actual_run" / "neutral_run_report.json"),
                prepared.scorer_answer_key,
                "--output",
                str(paths["scorer"] / "scorer_results" / "official_readiness_score.local.json"),
                "--sanitized-summary-output",
                str(paths["scorer"] / "scorer_results" / "official_readiness_summary.local.json"),
            ],
            paths["scorer"],
            timeout=60,
            pythonpath="src",
        )
    )
    gates.append(_run_command_gate("schema-field-plan", [sys.executable, "-m", "schema_field_envelope_planner.cli", prepared.schema_matrix, prepared.schema_plan_output], paths["schema_planner"], timeout=60, pythonpath="src"))
    gates.append(_run_command_gate("multi-llm-exposure-dry-run", [sys.executable, "-m", "multi_llm_representation_runner.cli", prepared.exposure_manifest, str(paths["llm_exposure"] / "outputs" / "official_dry_run"), "--dry-run"], paths["llm_exposure"], timeout=60, pythonpath="src"))
    gates.append(
        _run_command_gate(
            "public-free-llm-one-event-packets",
            [
                sys.executable,
                "-m",
                "multi_llm_representation_runner.free_llm_packets",
                str(paths["neutral"] / "outputs" / "official_readiness" / "actual_run" / "neutral_run_report.json"),
                str(paths["llm_exposure"] / "outputs" / "official_one_event_readiness"),
                "--max-packets",
                "3",
                "--selected-source-events-per-packet",
                "1",
                "--max-prompt-chars",
                "12000",
                "--max-pair-submission-delta-ms",
                "1000",
            ],
            paths["llm_exposure"],
            timeout=120,
            pythonpath="src",
        )
    )
    gates.append(_check_free_llm_manifest(Path(prepared.free_llm_manifest)))
    gates.extend(_check_tsel_bundles(paths["tsel"]))
    gates.append(_run_command_gate("reproducibility-manifest", [sys.executable, "-m", "reproducibility_evidence_packager.cli", prepared.evidence_manifest, str(paths["repro"] / "outputs" / "official_readiness" / "evidence_report.json"), "--allow-external"], paths["repro"], timeout=60, pythonpath="src"))
    gates.append(_check_public_web_pilot(paths["llm_exposure"] / "outputs" / "public_free_llm_pilot_2026-08-14"))

    warnings.append("Public free-LLM web interfaces do not expose stable exact model versions in every case; record the visible site, mode, date, screenshots, integrity token, and raw response without inferring an unshown version.")
    blocking_failures = [gate for gate in gates if gate.blocking and not gate.passed]
    report = ReadinessReport(
        ready=not blocking_failures,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        gates=gates,
        warnings=warnings,
        prepared=prepared,
    )
    report_path = Path(__file__).resolve().parents[2] / "reports" / "readiness_report.json"
    _write_json(report_path, report.to_record())
    return report


def run_pilot(base: str | Path | None = None) -> ReadinessReport:
    report = run_readiness(base)
    if not report.ready:
        return report
    paths = _paths(base)
    pilot_gates = list(report.gates)
    pilot_dir = paths["neutral"] / "outputs" / "pilot_first_five_actual"
    pilot_gates.append(_run_neutral_pilot(paths, pilot_dir))
    pilot_key = paths["scorer"] / "private_answer_keys" / "pilot_first_five_status_key.local.json"
    _write_json(pilot_key, _subset_answer_key(Path(report.prepared.scorer_answer_key), 5))
    pilot_gates.append(
        _run_command_gate(
            "pilot-private-scorer-first-five",
            [
                sys.executable,
                "-m",
                "private_answer_key_scorer.cli",
                str(pilot_dir / "neutral_run_report.json"),
                str(pilot_key),
                "--output",
                str(paths["scorer"] / "scorer_results" / "pilot_first_five_score.local.json"),
                "--sanitized-summary-output",
                str(paths["scorer"] / "scorer_results" / "pilot_first_five_summary.local.json"),
            ],
            paths["scorer"],
            timeout=60,
            pythonpath="src",
        )
    )
    ready = all(gate.passed or not gate.blocking for gate in pilot_gates)
    pilot_report = ReadinessReport(ready=ready, generated_at=datetime.now(UTC).isoformat(timespec="seconds"), gates=pilot_gates, warnings=report.warnings, prepared=report.prepared)
    _write_json(Path(__file__).resolve().parents[2] / "reports" / "pilot_report.json", pilot_report.to_record())
    return pilot_report


def _paths(base: str | Path | None) -> dict[str, Path]:
    root = _base(base)
    return {key: (root / rel).resolve() for key, rel in PROJECTS.items()}


def _base(base: str | Path | None) -> Path:
    if base is not None:
        return Path(base).resolve()
    return Path(__file__).resolve().parents[3]


def _public_mock_manifest(dataset: Path) -> dict[str, Any]:
    summary = _load_json(dataset / "generation_summary.json")
    return {
        "manifest_id": "thesis-blind-olfactory-validation-001",
        "manifest_type": "public_mock_manifest",
        "is_mock": True,
        "mock_label": "MOCK DATA - NOT REAL",
        "generator_run_id": "blind_olfactory_validation_001",
        "seed_ref": "SOURCE_DATA.md seed 84001",
        "construction_rules_ref": "README.md generate-blind-dataset and SOURCE_DATA.md",
        "artifacts": [
            {
                "artifact_id": "blind_olfactory_validation_001",
                "artifact_type": "mock_generator_output",
                "is_mock": True,
                "mock_label": "MOCK DATA - NOT REAL",
                "location": _relative_from_project(dataset),
                "evaluation_feed": _relative_from_project(dataset / "dataset_batch_manifest.json"),
                "packet_count": summary.get("public_packet_count", len(summary.get("public_packet_ids", []))),
            }
        ],
        "private_answer_key_included": False,
    }


def _neutral_packet_manifests(dataset: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    packet_ids = sorted(path.name for path in dataset.glob("mock_olfactory_packet_*") if path.is_dir())
    packets = [
        {
            "packet_id": packet_id,
            "packet_path": str(dataset / packet_id / "batch_manifest.json"),
            "output_path": "{packet_id}.bundle.json",
            "domain": "olfaction",
            "profile": "olfaction",
        }
        for packet_id in packet_ids
    ]
    pilot = {"manifest_version": "neutral-blind/v1", "description": "First five packet pilot subset.", "packets": packets[:5]}
    official = {
        "manifest_version": "neutral-blind/v1",
        "description": "Official public blind olfactory packet manifest. Contains no private labels or answer-key fields.",
        "packets": packets,
    }
    return official, pilot


def _neutral_runner_config(neutral_manifest: Path, tsel_repo: Path, *, dry_run: bool) -> dict[str, Any]:
    command = f"$env:PYTHONPATH='{tsel_repo}'; python -m tsel.cli batch '{{input_path}}' '{{output_path}}' --format bundle"
    return {
        "manifest": str(neutral_manifest),
        "output_dir": str(neutral_manifest.parent / ("dry_run" if dry_run else "actual_run")),
        "dry_run": dry_run,
        "timeout_seconds": 30,
        "fail_fast": dry_run,
        "command": ["powershell", "-NoProfile", "-Command", command],
    }


def _scorer_answer_key(answer_key_path: Path) -> dict[str, Any]:
    source = _load_json(answer_key_path)
    dataset = answer_key_path.parent
    packets = []
    for packet_id in sorted(source):
        row = source[packet_id]
        condition = str(row.get("condition", "")).strip().lower()
        packet_manifest = dataset / packet_id / "batch_manifest.json"
        jobs = _load_json(packet_manifest).get("jobs", []) if packet_manifest.exists() else []
        if not jobs or condition == "malformed":
            expected_status = "safe_failure"
        else:
            expected_status = "valid_encoding"
        packets.append({"packet_id": packet_id, "expected_status": expected_status})
    return {
        "answer_key_id": "official-status-key-local",
        "contract": "private-answer-key-scorer/v1",
        "source_private_key_sha256": _sha256(answer_key_path),
        "mapping_policy": "runner-contract status key: packets with public jobs expect valid_encoding; empty-job or malformed packets expect safe_failure. Semantic partiality is scored by timeline/missingness evaluators, not by neutral runner exit status.",
        "packets": packets,
    }


def _write_representations(neutral_run_report: Path, output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = _load_json(neutral_run_report)
    successful = [row for row in report.get("packets", []) if row.get("status") == "success" and row.get("output_path")]
    if len(successful) < 3:
        raise ValueError(f"one-event readiness matrix requires at least three successful mock-generator packets; found {len(successful)}")
    representations: dict[str, str] = {}
    for packet in successful[:3]:
        case_id = str(packet["packet_id"])
        events = _load_events(Path(str(packet["output_path"])), limit=1)
        if len(events) != 1:
            raise ValueError(f"readiness representation must contain exactly one source event: {case_id}")
        flat_path = output_dir / f"{case_id}__flat.json"
        flat_path.write_text(_render_flat(events), encoding="utf-8")
        for pattern_id, fields, scope in FIELD_ENVELOPES:
            if scope != "thesis":
                continue
            tsel_path = output_dir / f"{case_id}__{pattern_id}.json"
            tsel_path.write_text(_render_tsel_fields(events, fields), encoding="utf-8")
            representations[f"{case_id}__{pattern_id}__tsel"] = str(tsel_path)
            representations[f"{case_id}__{pattern_id}__flat"] = str(flat_path)
    return representations


def _schema_matrix(representations: dict[str, str]) -> dict[str, Any]:
    conditions: list[dict[str, Any]] = []
    case_ids = _representation_case_ids(representations)
    for case_id in case_ids:
        for pattern_id, fields, scope in FIELD_ENVELOPES:
            if scope != "thesis":
                continue
            family = pattern_id.removeprefix("tsel_")
            conditions.extend(
                [
                    _condition(case_id, pattern_id, family, "tsel", scope, fields, representations[f"{case_id}__{pattern_id}__tsel"]),
                    _condition(case_id, f"flat_for_{pattern_id}", family, "flat", scope, fields, representations[f"{case_id}__{pattern_id}__flat"]),
                ]
            )
    return {
        "research_questions": RESEARCH_QUESTIONS,
        "quality_controls": QUALITY_CONTROLS,
        "publication_scope_excluded_from_thesis": PUBLICATION_SCOPE,
        "official_fields": OFFICIAL_FIELDS,
        "publication_candidate_fields_excluded_from_thesis": CANDIDATE_FIELDS,
        "one_event_per_representation": True,
        "simultaneous_flat_tsel_pair_required": True,
        "cases": [{"case_id": case_id, "questions": QUESTION_SET} for case_id in case_ids],
        "models": [_echo_model()],
        "conditions": conditions,
    }


def _condition(case_id: str, suffix: str, family: str, kind: str, scope: str, fields: list[str], artifact: str) -> dict[str, Any]:
    return {
        "condition_id": f"{case_id}_{suffix}",
        "condition_family": family,
        "representation_kind": kind,
        "study_scope": scope,
        "fields": fields,
        "artifact_path": artifact,
        "control_pair_id": f"{case_id}_{family}",
    }


def _exposure_manifest(representations: dict[str, str]) -> dict[str, Any]:
    matrix = _schema_matrix(representations)
    cases = []
    for case in matrix["cases"]:
        case_id = case["case_id"]
        case_conditions = [row for row in matrix["conditions"] if row["condition_id"].startswith(f"{case_id}_")]
        cases.append(
            {
                "case_id": case_id,
                "included_event_count": 1,
                "representations": {row["condition_id"]: row["artifact_path"] for row in case_conditions},
                "questions": QUESTION_SET,
            }
        )
    return {"research_questions": RESEARCH_QUESTIONS, "study_role": "local readiness dry run only", "one_event_per_prompt": True, "models": [_echo_model()], "cases": cases}


def _representation_case_ids(representations: dict[str, str]) -> list[str]:
    suffix = f"__{FIELD_ENVELOPES[0][0]}__tsel"
    return sorted(key[: -len(suffix)] for key in representations if key.endswith(suffix))


def _echo_model() -> dict[str, Any]:
    return {
        "model_id": "local_echo_adapter_for_readiness",
        "command": [sys.executable, "-c", "from pathlib import Path; import sys; print(Path(sys.argv[1]).read_text(encoding='utf-8')[:200])", "{prompt_path}"],
    }


def _evidence_manifest(*paths: Path) -> dict[str, Any]:
    files = []
    for path in paths:
        if path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    files.append({"path": str(child), "role": "generated_readiness_artifact"})
        else:
            files.append({"path": str(path), "role": "generated_readiness_artifact"})
    return {"manifest_id": "thesis-readiness-evidence-local", "research_questions": RESEARCH_QUESTIONS, "files": files}


def _check_repositories(paths: dict[str, Path]) -> list[Gate]:
    gates = []
    for key, path in paths.items():
        gates.append(Gate(f"repo-exists-{key}", path.exists() and (path / ".git").exists(), str(path)))
    return gates


def _suite_command(base: Path) -> list[str]:
    script = (
        "$ErrorActionPreference='Stop'; "
        "$projects=Get-ChildItem -LiteralPath . -Directory | Where-Object {$_.Name -match '^\\d{2}_'} | Sort-Object Name; "
        "foreach($p in $projects){ Push-Location $p.FullName; $env:PYTHONPATH='src'; python -m pytest -q; if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }; Pop-Location }"
    )
    return ["powershell", "-NoProfile", "-Command", script]


def _run_command_gate(name: str, command: list[str], cwd: Path, *, timeout: int, pythonpath: str | None = None) -> Gate:
    env = os.environ.copy()
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    try:
        completed = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return Gate(name, False, f"{type(exc).__name__}: {exc}")
    detail = (completed.stdout + "\n" + completed.stderr).strip()
    return Gate(name, completed.returncode == 0, detail[-1000:] if detail else "ok")


def _run_neutral_pilot(paths: dict[str, Path], pilot_dir: Path) -> Gate:
    command = [
        sys.executable,
        "-m",
        "neutral_blind_runner.cli",
        str(paths["neutral"] / "outputs" / "official_readiness" / "pilot_public_packet_manifest.json"),
        str(pilot_dir),
        "--command",
        "powershell",
        "-NoProfile",
        "-Command",
        f"$env:PYTHONPATH='{paths['tsel']}'; python -m tsel.cli batch '{{input_path}}' '{{output_path}}' --format bundle",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    try:
        completed = subprocess.run(command, cwd=paths["neutral"], env=env, capture_output=True, text=True, timeout=180)
    except Exception as exc:
        return Gate("pilot-neutral-first-five", False, f"{type(exc).__name__}: {exc}")
    report_path = pilot_dir / "neutral_run_report.json"
    if not report_path.exists():
        return Gate("pilot-neutral-first-five", False, "neutral_run_report.json was not created")
    report = _load_json(report_path)
    statuses = report.get("statuses", {})
    allowed = set(statuses) <= {"success", "safe_failure"}
    detail = (completed.stdout + "\n" + completed.stderr).strip()
    return Gate("pilot-neutral-first-five", allowed, detail[-1000:] if detail else json.dumps(statuses, sort_keys=True))


def _run_neutral_official(paths: dict[str, Path], config_path: Path) -> Gate:
    command = [sys.executable, "-m", "neutral_blind_runner.cli", "--config", str(config_path)]
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    try:
        completed = subprocess.run(command, cwd=paths["neutral"], env=env, capture_output=True, text=True, timeout=300)
    except Exception as exc:
        return Gate("neutral-blind-actual-run", False, f"{type(exc).__name__}: {exc}")
    report_path = paths["neutral"] / "outputs" / "official_readiness" / "actual_run" / "neutral_run_report.json"
    if not report_path.exists():
        return Gate("neutral-blind-actual-run", False, "neutral_run_report.json was not created")
    report = _load_json(report_path)
    packets = report.get("packets", [])
    statuses = report.get("statuses", {})
    allowed = (
        isinstance(packets, list)
        and len(packets) == 90
        and isinstance(statuses, dict)
        and set(statuses) <= {"success", "safe_failure"}
        and sum(int(value) for value in statuses.values()) == 90
    )
    detail = {
        "command_exit_code": completed.returncode,
        "packet_count": len(packets) if isinstance(packets, list) else None,
        "statuses": statuses,
        "policy": "success and safe_failure are both eligible for private expected-status scoring",
    }
    return Gate("neutral-blind-actual-run", allowed, json.dumps(detail, sort_keys=True))


def _subset_answer_key(answer_key_path: Path, count: int) -> dict[str, Any]:
    key = _load_json(answer_key_path)
    packets = key.get("packets", [])
    if not isinstance(packets, list):
        raise ValueError("answer key packets must be a list")
    subset = dict(key)
    subset["answer_key_id"] = f"{key.get('answer_key_id', 'answer-key')}-first-{count}"
    subset["packets"] = packets[:count]
    return subset


def _check_json_gate(name: str, path: Path, checker) -> Gate:
    try:
        payload = _load_json(path)
        checker(payload)
    except Exception as exc:
        return Gate(name, False, str(exc))
    return Gate(name, True, str(path))


def _check_scorer_key(payload: dict[str, Any]) -> None:
    packets = payload.get("packets")
    if not isinstance(packets, list) or len(packets) != 90:
        raise ValueError("scorer key must contain 90 packets")
    allowed = {"valid_encoding", "valid_partial_encoding", "safe_failure"}
    for packet in packets:
        if packet.get("expected_status") not in allowed:
            raise ValueError(f"unsupported expected_status for {packet.get('packet_id')}")


def _check_tsel_bundles(tsel: Path) -> list[Gate]:
    gates = []
    for name in ("olfactory_gas.bundle.json", "synapse_olfaction.bundle.json"):
        bundle = tsel / "output" / "thesis_validation" / name
        gates.append(_run_command_gate(f"tsel-validate-{name}", [sys.executable, "-m", "tsel.cli", "validate", str(bundle), "--strict"], tsel, timeout=120))
        gates.append(_run_command_gate(f"tsel-conformance-{name}", [sys.executable, "-m", "tsel.cli", "conformance", str(bundle), "--strict"], tsel, timeout=120))
    return gates


def _check_free_llm_manifest(path: Path) -> Gate:
    try:
        manifest = _load_json(path)
        rows = manifest.get("rows", [])
        pairs = manifest.get("matched_pairs", [])
        if not manifest.get("one_event_per_prompt") or not manifest.get("simultaneous_pair_submission_required"):
            raise ValueError("manifest lacks one-event or simultaneous-pair controls")
        if not manifest.get("fresh_isolated_context_per_prompt_required"):
            raise ValueError("manifest permits shared prompt context")
        if manifest.get("max_pair_submission_delta_ms") != 1_000:
            raise ValueError("manifest does not enforce the 1,000 ms simultaneous-submission window")
        if not manifest.get("both_submitted_before_either_response_visible_required"):
            raise ValueError("manifest permits one response to appear before the matched prompt is submitted")
        if not rows or not pairs:
            raise ValueError("manifest contains no prompt rows or matched pairs")
        if any(row.get("included_event_count") != 1 for row in rows):
            raise ValueError("a prompt row contains more or fewer than one event")
        for pair in pairs:
            pair_rows = [row for row in rows if row.get("pair_id") == pair.get("pair_id")]
            if len(pair_rows) != 2 or {row.get("pair_role") for row in pair_rows} != {"flat", "comparison"}:
                raise ValueError(f"invalid matched pair: {pair.get('pair_id')}")
            if len({row.get("event_id") for row in pair_rows}) != 1:
                raise ValueError(f"pair does not use one identical source event: {pair.get('pair_id')}")
            if len({row.get("source_event_index") for row in pair_rows}) != 1:
                raise ValueError(f"pair does not use one identical source-event index: {pair.get('pair_id')}")
            if len({row.get("question_id") for row in pair_rows}) != 1:
                raise ValueError(f"pair does not use one identical question: {pair.get('pair_id')}")
            if len({row.get("public_pair_id") for row in pair_rows}) != 1:
                raise ValueError(f"pair lacks one opaque public pair ID: {pair.get('pair_id')}")
            if pair.get("max_submission_delta_ms") != 1_000:
                raise ValueError(f"pair lacks the simultaneous-submission window: {pair.get('pair_id')}")
            if not pair.get("both_submitted_before_either_response_visible_required"):
                raise ValueError(f"pair permits sequential response exposure: {pair.get('pair_id')}")
            execution_form = path.parent / str(pair.get("pair_execution_form", ""))
            if not execution_form.is_file():
                raise ValueError(f"pair lacks its execution evidence form: {pair.get('pair_id')}")
            execution = _load_json(execution_form)
            if execution.get("included_event_count_per_prompt") != 1 or not execution.get("same_source_event_required"):
                raise ValueError(f"pair execution form violates the one-event matched-pair rule: {pair.get('pair_id')}")
            if execution.get("max_submission_delta_ms") != 1_000:
                raise ValueError(f"pair execution form lacks the simultaneous-submission window: {pair.get('pair_id')}")
    except Exception as exc:
        return Gate("public-free-llm-manifest-contract", False, str(exc))
    return Gate("public-free-llm-manifest-contract", True, f"{len(pairs)} matched one-event pairs; {len(rows)} prompts")


def _check_public_web_pilot(path: Path) -> Gate:
    required_sites = ["one_event_simultaneous", "copilot_one_event_simultaneous", "perplexity_one_event_simultaneous"]
    missing: list[str] = []
    for site_dir in required_sites:
        folder = path / site_dir
        if not (folder / "run_log.json").exists():
            missing.append(f"{site_dir}/run_log.json")
        if len(list(folder.glob("*.png"))) < 2:
            missing.append(f"{site_dir} screenshots")
    if missing:
        return Gate("public-web-pilot-evidence", False, "missing: " + ", ".join(missing), blocking=False)
    return Gate("public-web-pilot-evidence", True, "Gemini, Copilot, and Perplexity one-event pilot logs and screenshots present", blocking=False)


def _load_events(path: Path, *, limit: int) -> list[dict[str, Any]]:
    payload = _load_json(path)
    events = payload.get("events") if isinstance(payload, dict) else None
    if not isinstance(events, list):
        raise ValueError(f"bundle has no events list: {path}")
    return [event for event in events[:limit] if isinstance(event, dict)]


def _render_tsel_fields(events: list[dict[str, Any]], fields: list[str]) -> str:
    if len(events) != 1:
        raise ValueError("prompt representation must contain exactly one event")
    rows = []
    for event in events:
        row: dict[str, Any] = {}
        for field in fields:
            if field in OFFICIAL_FIELDS:
                row[field] = event.get(field)
            elif field == "assertion_basis":
                row[field] = event.get("contextual_metadata", {}).get("assertion_basis")
            elif field == "collection_quality":
                row[field] = {
                    "completeness": event.get("contextual_metadata", {}).get("completeness"),
                    "unresolved": event.get("contextual_metadata", {}).get("unresolved"),
                }
        rows.append(row)
    return json.dumps(rows, indent=2, sort_keys=True)


def _render_flat(events: list[dict[str, Any]]) -> str:
    if len(events) != 1:
        raise ValueError("flat prompt representation must contain exactly one event")
    rows = []
    for event in events:
        context = event.get("contextual_metadata", {})
        completeness = context.get("completeness", {}) if isinstance(context, dict) else {}
        missing_dimensions = completeness.get("missing_dimensions", []) if isinstance(completeness, dict) else []
        rows.append(
            {
                "time": event.get("timestamp"),
                "sense_or_modality": event.get("modality"),
                "source_id": event.get("source"),
                "measurement": event.get("signal_type"),
                "observed_value": event.get("value"),
                "observed_unit": event.get("unit"),
                "missing_odor_concentration": "odor_concentration" in {str(item) for item in missing_dimensions} if isinstance(missing_dimensions, list) else False,
            }
        )
    return json.dumps(rows, indent=2, sort_keys=True)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_from_project(path: Path) -> str:
    return str(Path("..") / path.name) if path.is_file() else str(path)
