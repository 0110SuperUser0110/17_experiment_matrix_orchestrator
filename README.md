# Experiment Matrix Orchestrator

Local orchestration tool for checking the evidence required by the two ARB-approved TSEL thesis questions and coordinating independent testing projects.

The thesis design treats seven as the width of the named TSEL envelope, not as a claim that all seven values must always be populated. The structural study exhaustively evaluates all 128 populated/empty masks while retaining every named key. The approved heterogeneous evaluation applies the four ARB feasibility criteria to five simulated datasets. Public-model exposure and fields beyond seven are publication-only workstreams and do not gate thesis readiness.

This repository is a research tool. It does not belong inside the TSEL repository and does not replace the individual testing projects. It prepares local run artifacts, checks project boundaries, validates manifests, and writes readiness reports before official data collection.

## Current Status

Maturity: research-tool alpha.

Implemented:

- Checks the repositories required by the two approved RQs, including the independent heterogeneous-dataset evaluator.
- Builds local official manifests for mock-generator coordination, neutral TSEL processing, private scoring, the complete one-through-seven field envelope, publication-scope candidate fields, public free-LLM exposure, and reproducibility packaging.
- Keeps generated run files under ignored `work/`, `outputs/`, and downstream project output/private folders.
- Converts the rich private olfactory answer key into the stricter local scorer contract without putting private expectations in public manifests.
- Runs approved-thesis readiness gates and returns a non-zero exit code when any required repository, dataset criterion, occupancy check, or evidence hash fails.
- Runs TSEL against the mock-generator packets before building study prompts.
- Enforces exactly one source event per prompt and one explicit flat-versus-TSEL comparison per matched pair.
- Requires each pair to be submitted in separate fresh chats within 1,000 milliseconds, with both prompts sent before either response becomes visible.
- Validates the browser-based public free-LLM manifest, prompt budget, and evidence-capture contract.
- Runs a local pilot using neutral packet validation and dry-run exposure planning.

The public free-LLM collection path is retained for post-thesis publication work. It is intentionally manual and browser based and does not affect the approved thesis readiness result.

## Usage

From this repository root:

```powershell
$env:PYTHONPATH = "src"
python -m experiment_matrix_orchestrator.cli prepare
python -m experiment_matrix_orchestrator.cli readiness
python -m experiment_matrix_orchestrator.cli pilot
python -m experiment_matrix_orchestrator.cli final-data-readiness
```

`final-data-readiness` returns `0` only when the two-RQ approved thesis evidence is complete. Publication-only model-exposure artifacts are excluded from this command's gates.

Run tests:

```powershell
python -m pytest -q
```

## Trust Boundaries

- TSEL remains an external artifact.
- Testing projects remain independent repositories under the shared project base.
- Public manifests must not include answer-key fields.
- Private key transformations are written only to ignored local folders.
- Exactly two research questions appear in thesis readiness output.
- Inspectability, reproducibility, and mock labeling are quality controls, not a third thesis RQ.
- Heterogeneous evaluation code and evidence remain in repository 18, outside TSEL.
- Publication-only field candidates and public-model exposures remain explicitly excluded from thesis readiness.
- Each free-LLM prompt contains one event. The flat and TSEL prompts in a pair use the identical source event and question, public pair IDs are opaque, and events are never combined into a prompt stream or shared chat context.
- Readiness requires a pair execution form for UTC submission times, measured submission gap, separate chat identifiers, visible model/mode, and four prompt/response screenshots.
- Each TSEL field condition receives a fresh strict-flat control built from the identical event and question.
- Public-web evidence requires prompt and response screenshots, raw response logs, visible site or model labels, timestamps, and delivery-integrity results.

## License Status

No redistribution license has been selected. Treat this as internal thesis tooling unless a license is added.
