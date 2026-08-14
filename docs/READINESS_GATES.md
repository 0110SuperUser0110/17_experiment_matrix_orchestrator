# Readiness Gates

The orchestrator checks readiness in this order:

1. Required repositories exist and are independent Git repositories.
2. Required source dataset and TSEL bundle files exist.
3. Public mock manifest validates without private answer-key fields.
4. Neutral blind public packet manifest dry-runs successfully.
5. Private answer key can be transformed into the scorer contract.
6. Schema field envelope plan validates the seven official fields, reduced-field thesis ablations, flat controls, and publication-scope candidate fields.
7. Multi-LLM exposure manifest dry-runs with controlled representations.
8. Existing TSEL thesis bundles validate and pass conformance without errors.
9. Reproducibility evidence manifest can be built from the generated local artifacts.
10. External collection is allowed only if no gate fails and model adapters are configured.

Warnings do not block pilot collection unless they represent private leakage, missing artifacts, unscoreable outputs, or conformance errors. Synapse noncanonical signal-type warnings require a thesis policy before final result claims.
