# Verification

When investigating or fixing a transition-state search failure, run
`pixi run -e dev test-ts`, the opt-in real chemistry regression set. Add a
deterministic case for any newly reported failing molecule. A focused case is
useful during debugging, but run the complete set before finishing and report
any failures. Keep these expensive tests disabled in default test runs.
