# Working Workflow

**Status: PROPOSED — use this workflow unless the Game Director changes it.**

This document describes how the project team assigns work, coordinates AI agents, reviews changes, and keeps decisions durable. The Game Director / Head Designer (human) has final authority over game direction.

## 1. Roles and ownership

- **Game Director (human):** sets priorities, approves major design changes, resolves conflicts, accepts or rejects deliverables, and decides what enters the main branch.
- **Lead Agent / Documentation & Knowledge Manager (ChatGPT):** turns goals into bounded tasks, assigns a single owner, tracks cross-document consistency, records decisions, reviews handoffs, and escalates design questions. The Lead Agent does not silently decide major game-design questions.
- **Technical Design Agent:** owns architecture proposals, system boundaries, data models, interfaces, and technical trade-off analysis.
- **Programming Agent:** owns implementation of an approved task, including focused tests and implementation notes.
- **Build / Tools Agent:** owns developer setup, test commands, automation, reproducible simulations, and build/debug tooling.
- **Human playtesters:** provide observations about usability, comprehension, pacing, and player experience. Their feedback is evidence, not an automatic design mandate.

Start with these roles only. Do not add an agent unless recurring workload or a clear specialist need justifies it.

## 2. Task lifecycle

1. **Intake:** The Game Director states the desired outcome. The Lead Agent identifies scope, priority, dependencies, and the smallest useful deliverable.
2. **Task brief:** Before substantial work, write down the owner, goal, in-scope and out-of-scope work, acceptance criteria, relevant files, assumptions, and questions that require approval.
3. **Proposal:** The owner summarizes the approach before changing behavior, interfaces, architecture, or approved design. For small, reversible tasks within existing decisions, implementation may begin directly.
4. **Decision gate:** Ask the Game Director before changing core mechanics, player-facing behavior, scope, persistence formats, major architecture, dependencies with lasting cost, or any approved decision. Continue independent work while waiting when possible.
5. **Implementation:** Work in a focused branch or isolated patch. Keep changes small, avoid unrelated cleanup, and add or update tests when behavior changes.
6. **Handoff:** The owner reports the actual changes, checks run and results, assumptions, unresolved questions, and suggested next step.
7. **Review:** The Lead Agent checks acceptance criteria, consistency with approved decisions, scope, and test evidence. A specialist agent may review high-risk technical work. Reviewers comment or propose patches; they do not overwrite the owner's work.
8. **Acceptance:** The Game Director decides whether the work is accepted and whether it should merge. Merge only after review and required checks.
9. **Record:** Update `DECISIONS.md` for approved decisions, relevant design docs for lasting rules, and `PLAYTEST_NOTES.md` for observations. Do not use chat history as the only record.

## 3. Decision rules

Use these labels consistently:

- **APPROVED:** explicitly accepted by the Game Director or already covered by an approved decision.
- **PROVISIONAL:** a current working assumption that can be revised.
- **PROPOSED:** awaiting a decision.
- **EXPERIMENTAL:** tested or simulated for exploration, not validated as a rule.
- **DEFERRED:** intentionally postponed.
- **REJECTED:** considered and not accepted.

If instructions conflict, use this order: (1) the Game Director's most recent explicit direction, (2) approved entries in `DECISIONS.md`, (3) approved design documents, (4) implemented code and tests as evidence of current behavior, (5) proposals, experiments, playtest notes, and summaries. Code that contradicts an approved design is a discrepancy to report, not permission to silently redefine the design.

Ask the Game Director when a decision is consequential, hard to reverse, player-facing, or changes scope. Otherwise choose the simplest maintainable option consistent with existing decisions and document the assumption.

## 4. Repository and change rules

- Treat `main` as the accepted baseline. Do not commit experimental or incomplete work directly to `main`.
- Use one focused branch or patch per task; name branches descriptively, for example `docs/clarify-agent-handoff` or `feat/persistent-death-bonus`.
- Keep pull requests small and explain purpose, scope, tests, risks, and open questions.
- Do not overwrite another agent's branch or files. Ask the owner to revise, or submit review comments/a separate patch.
- Never claim a test, simulation, or manual check was run unless it actually was. Include exact commands and results where possible.
- Do not add dependencies, change save formats, or restructure modules without a stated reason and appropriate review.
- Keep secrets, API keys, private tokens, and personal credentials out of the repository and prompts.
- If a tool cannot access or modify a resource, say so plainly and provide a patch or instructions rather than implying the change was made.

## 5. Task brief template

Use this template for work that is more than a trivial edit:

```text
Task:
Owner:
Goal / player or developer value:
Scope:
Out of scope:
Relevant files and decisions:
Acceptance criteria:
Constraints:
Assumptions:
Questions requiring Game Director approval:
Deliverable format:
```

A task should normally have one accountable owner. Other agents can be reviewers or consultants, not co-owners with ambiguous responsibility.

## 6. Handoff template

Every substantial task ends with:

```text
Summary:
Files changed:
Behavior or decisions affected:
Tests/checks run:
Results:
Assumptions:
Open questions / risks:
Recommended next step:
```

If no files changed, state that explicitly. If tests were not run, say why.

## 7. How to use external AI agents

1. Open the relevant provider/model and give it the role prompt from `agents/`.
2. Provide the task brief and only the repository files needed for that task. Link to the repository, but do not assume a model can access it; paste or attach relevant files if necessary.
3. Tell the agent to treat repository decisions as source of truth, mark proposals as proposals, and return a patch/diff or clearly identified replacement files.
4. Ask for a handoff using the template above. Require it to distinguish verified checks from suggested checks.
5. Bring the result back to the Lead Agent for consistency review, then to the Game Director for any required approval.
6. Only after acceptance should the work be merged and durable decisions recorded.

Agents do not automatically share memory or conversation context. The task brief and repository files must contain the context an agent needs. Use model choice pragmatically; do not split a small task among multiple agents just to create parallel work.

## 8. Initial operating cadence

For the first prototype, use this lightweight cadence:

- One active implementation task at a time, plus at most one independent design/tooling investigation.
- Technical Design proposes interfaces when a feature needs new structure; Programming implements only after required design approval.
- Build / Tools verifies setup and repeatable checks, and can create small reproducible experiments. Experimental results must include code or commands, assumptions, and seed/configuration where relevant.
- The Lead Agent maintains documentation and raises conflicts or missing decisions.
- The Game Director reviews the task brief when scope is set and the deliverable at acceptance. Routine implementation details do not need repeated approval.

Review this workflow after the first complete playable loop or after several tasks reveal a specific bottleneck. Change it based on observed friction rather than adding process pre-emptively.
