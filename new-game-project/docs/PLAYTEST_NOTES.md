# Playtest Notes
Separate observations from interpretation and decisions.

## Session template
- Date/build:
- Tester label (non-identifying):
- Session length:
- Goal:
- Observed behavior:
- Player comments:
- Confusion/friction:
- Unexpected behavior:
- Potential changes:
- Follow-up questions:

## EXPERIMENTAL — Telegraphed heavy attack (pending playtest)
Branch: `experiment/telegraphed-heavy-attack`. Not an approved rule; keep, revise, or remove after playtesting.

**Rule under test:** with `python -m game.sim --heavy`, the enemy repeats attack → wind up → heavy attack. The wind-up prints a warning and gives the player one turn to respond. The heavy attack deals normal damage +3 (5 with the default enemy), is blocked by Defend, and happens once per wind-up.

**How to compare:** play a few encounters with `python -m game.sim` (baseline), then a few with `python -m game.sim --heavy`.

**Known before playtesting (from tests, not players):**
- In the baseline, the player's choice of Attack or Defend never changes who wins. With `--heavy` it can: for example, player Puissant 3 / HP 7 against the default enemy loses by attacking through the heavy attack and wins by defending.
- With the default prototype stats (player HP 12), the player wins every encounter whatever they choose; the choice only changes remaining HP (5–12). HP does not carry over between encounters, so at default stats Attack is not yet a real risk.

**Questions for this session:**
- Was the warning clear?
- Did choosing Defend feel useful?
- Did choosing Attack instead feel like a deliberate risk?
- Was the mechanic interesting enough to keep playing?
- Did anything feel confusing or unnecessarily slow?

**Session:**
- Date/build:
- Tester label (non-identifying):
- Observed behavior:
- Player comments:
- Confusion/friction:
- Potential changes:
