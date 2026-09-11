# Source integration map

## v4 PPA-GOV — primary UI/workflow baseline

The browser dashboard, navigation, colors, modules, Guided Demo, Infrastructure workflow, analyst workflow, privacy controls and operational pages are preserved from the v4 baseline.

## PPA-GOV research engine (`engine/`)

Integrated as the correctness/evaluation layer:

- DP-SGD and conservative RDP accounting
- federated training
- secure aggregation
- robust aggregation
- Laplace DP aggregate queries
- deterministic privacy-aware analyst agent
- query-pattern monitoring
- membership-inference evaluation
- gradient-inversion evaluation
- model-poisoning evaluation
- reproducible experiment results and tests

## AEGIS

The AEGIS attack/detection concepts were reviewed and incorporated into the main Attack Lab and Threat Detection rather than shipping a second disconnected dashboard. Integrated scenarios are:

- membership inference
- differencing attack
- rare subgroup reconstruction
- repeated-query attack
- gradient inversion
- model poisoning

The final UI remains PPA-GOV's existing color/layout system.

## PPGA

The two supplied PPGA synthetic datasets are included under `data/ppga/` as supplementary synthetic-data material. They are not silently mixed with the PPA-GOV research dataset, preventing accidental cross-project data contamination.

## Sentinel Kill Chain

The requested `sentinel-kill-chain (2).zip` was not among the files available to this build, so no Sentinel-specific code was guessed or fabricated. The existing v4 UI remains the visual baseline.
