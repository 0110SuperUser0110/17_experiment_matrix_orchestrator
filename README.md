# Experiment Matrix Orchestrator

Local orchestration tool for freezing thesis data-collection inputs and checking readiness across the independent TSEL testing projects.

This repository is a research tool. It does not belong inside the TSEL repository and does not replace the individual testing projects. It prepares local run artifacts, checks project boundaries, validates manifests, and writes readiness reports before official data collection.

## Current Status

Maturity: research-tool alpha.

Implemented:

- Checks TSEL, the mock generator, and all 17 independent testing repositories.
- Builds local official manifests for mock-generator coordination, neutral TSEL processing, private scoring, the complete one-through-seven field envelope, publication-scope candidate fields, public free-LLM exposure, and reproducibility packaging.
- Keeps generated run files under ignored `work/`, `outputs/`, and downstream project output/private folders.
- Converts the rich private olfactory answer key into the stricter local scorer contract without putting private expectations in public manifests.
- Runs readiness gates and returns a non-zero exit code when any gate fails.
- Runs TSEL against the mock-generator packets before building study prompts.
- Enforces exactly one source event per prompt and one explicit flat-versus-TSEL comparison per matched pair.
- Requires each pair to be submitted simultaneously in separate fresh chats.
- Validates the browser-based public free-LLM manifest, prompt budget, and evidence-capture contract.
- Runs a local pilot using neutral packet validation and dry-run exposure planning.

The public free-LLM collection path is intentionally manual and browser based. It does not use provider APIs, credentials, or paid model adapters. Exact versions are recorded only when visibly exposed by the public interface; otherwise the site, visible mode, date, screenshots, raw response, and integrity result are retained without guessing a version.

## Usage

From this repository root:

```powershell
$env:PYTHONPATH = "src"
python -m experiment_matrix_orchestrator.cli prepare
python -m experiment_matrix_orchestrator.cli readiness
python -m experiment_matrix_orchestrator.cli pilot
```

Run tests:

```powershell
python -m pytest -q
```

## Trust Boundaries

- TSEL remains an external artifact.
- Testing projects remain independent repositories under the shared project base.
- Public manifests must not include answer-key fields.
- Private key transformations are written only to ignored local folders.
- Each free-LLM prompt contains one event. Events are never combined into a prompt stream.
- Each TSEL field condition receives a fresh strict-flat control built from the identical event and question.
- Public-web evidence requires prompt and response screenshots, raw response logs, visible site or model labels, timestamps, and delivery-integrity results.

## License Status

No redistribution license has been selected. Treat this as internal thesis tooling unless a license is added.
