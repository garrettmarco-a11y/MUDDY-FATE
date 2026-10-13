# Agent Protocol

## Roles
- **Game Director / Head Designer (human):** final authority on game direction and major design choices.
- **Lead Agent / Documentation & Knowledge Manager:** coordinates tasks, tracks consistency, records approved decisions, escalates major choices.
- **Technical Design Agent:** proposes architecture, interfaces, data models, and trade-offs.
- **Programming Agent:** implements approved scoped tasks and tests.
- **Build / Tools Agent:** maintains setup, tests, simulation tools, and scripts.
- **Human playtesters:** provide evidence about player experience.

## Workflow
1. Define a small task with scope and acceptance criteria.
2. Assigned agent reads relevant docs and reports assumptions/blockers.
3. Agent proposes approach before substantial work if behavior or interfaces may change.
4. Deliver a small diff, patch, branch, or isolated proposal.
5. Other agents may review and suggest changes but must not overwrite the original work.
6. Lead Agent checks consistency.
7. Game Director approves major design decisions.
8. Record approved decisions in `DECISIONS.md`.

## Source of truth
1. Explicit recent direction from Game Director
2. Approved entries in `DECISIONS.md`
3. Current approved design documents
4. Code/tests for what is implemented
5. Proposals, experiments, playtest notes, and old conversation summaries

## Labels
**APPROVED**, **PROVISIONAL**, **PROPOSED**, **EXPERIMENTAL**, **DEFERRED**, **REJECTED**.

Keep durable context in repository files so the workflow is provider-neutral. Role prompts should work across Claude, Gemini, DeepSeek, and other models.
