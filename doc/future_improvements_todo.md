# Future Improvements TODO

This list captures improvements to revisit later. Keep items small, testable, and aligned with the constitution.

## DDD Guardrails

- [ ] Add CI check to verify spec artifacts include bounded context, ubiquitous language, invariants, and external boundaries.
- [ ] Add CI check to verify plan artifacts include DDD impact and Constitution Check completion.
- [ ] Add CI check to verify tasks include DDD compliance task(s) for invariant and layer ownership validation.
- [ ] Add a review helper script to flag potential business logic leakage in interfaces/bootstrap/infrastructure/state modules.

## Developer Workflow

- [ ] Add a PR template section with mandatory DDD checklist responses.
- [ ] Add a short "How to model domain invariants" guide with examples for non-DDD specialists.
- [ ] Add a "minimal core vs domain/application" decision guide with concrete decision examples.

## Testing

- [ ] Add invariant-focused test examples in tests/unit as templates for future features.
- [ ] Add a smoke test that validates bootstrap + list-skills + state path expectations in one flow.
- [ ] Add coverage targets for domain and state-transition-heavy code paths.

## Documentation Hygiene

- [ ] Keep AGENTS.md and .github/copilot-instructions.md in lockstep with a periodic consistency check.
- [ ] Add a release checklist step to verify constitution/version alignment and guidance sync.
- [ ] Add a short changelog section for governance and process updates.

## Prioritization (when resumed)

1. CI checks for spec/plan/tasks DDD gates.
2. PR template with DDD checklist.
3. Domain invariants guide for non-specialists.
4. Business-logic leakage review helper.
