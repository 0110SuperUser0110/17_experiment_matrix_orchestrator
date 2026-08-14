# Experiment Matrix Orchestrator

Local orchestration tool for freezing thesis data-collection inputs and checking readiness across the independent TSEL testing projects.

This repository is a research tool. It does not belong inside the TSEL repository and does not replace the individual testing projects. It prepares local run artifacts, checks project boundaries, validates manifests, and writes readiness reports before official data collection.

## Current Status

Maturity: research-tool alpha.

Implemented:

- Builds local official manifests for the mock-generator coordination, neutral blind runner, private scorer, schema-envelope planner, multi-LLM exposure runner, and reproducibility packager.
- Keeps generated run files under ignored `work/`, `outputs/`, and downstream project output/private folders.
- Converts the rich private olfactory answer key into the stricter local scorer contract without putting private expectations in public manifests.
- Runs readiness gates and returns a non-zero exit code when any gate fails.
- Runs a local pilot using dry-run neutral packet validation and dry-run multi-LLM exposure planning.

Not implemented:

- Provider-specific LLM calls.
- Remote task creation.
- Git commits or pushes.
- License selection.

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
- External LLM collection is blocked until the model adapter commands and provider credentials are supplied outside this repository.

## License Status

No redistribution license has been selected. Treat this as internal thesis tooling unless a license is added.
