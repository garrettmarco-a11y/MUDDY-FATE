"""Terminal combat simulation for playtesting the basic combat loop.

Run from ``new-game-project/``::

    python -m game.sim           # baseline rules
    python -m game.sim --heavy   # EXPERIMENTAL telegraphed heavy attack

This module only handles presentation and input. Every combat rule (damage,
turn order, defeat, encounter end) comes from ``game.combat``. Input and
output are injected as ``read(prompt) -> str`` and ``write(text)`` so tests
can drive the simulation without a terminal.
"""

from __future__ import annotations

import argparse
from dataclasses import fields
from typing import Callable

from game.combat import (
    Action,
    AttackResult,
    Character,
    DefendResult,
    Encounter,
    Side,
    Traits,
    WindUpResult,
)

Read = Callable[[str], str]
Write = Callable[[str], None]

# PROTOTYPE VALUES: chosen only so a fight lasts a few turns. Not approved
# balance; only Puissant affects combat.
PLAYER_TRAITS = Traits(puissant=3, alacrity=2, measure=2, aptitude=1, acumen=1, glamour=1)
PLAYER_HEALTH = 12
ENEMY_TRAITS = Traits(puissant=2, alacrity=1, measure=1, aptitude=0, acumen=0, glamour=0)
ENEMY_HEALTH = 10

NAMES = {Side.PLAYER: "Player", Side.ENEMY: "Enemy"}

WON, LOST = "won", "lost"

# EXPERIMENTAL: with --heavy, the enemy follows a fixed, repeating script of
# attack, wind up, heavy attack. No randomness and no decision-making.
HEAVY_CYCLE = 3


def default_player() -> Character:
    return Character(PLAYER_TRAITS, health=PLAYER_HEALTH)


def default_enemy() -> Character:
    return Character(ENEMY_TRAITS, health=ENEMY_HEALTH)


def describe_character(side: Side, character: Character) -> str:
    traits = "  ".join(
        f"{f.name.capitalize()} {getattr(character.traits, f.name)}"
        for f in fields(Traits)
    )
    return f"{NAMES[side]:<6} HP {character.health:>3} | {traits}"


def describe_result(
    result: AttackResult | DefendResult | WindUpResult, encounter: Encounter
) -> str:
    if isinstance(result, DefendResult):
        return f"{NAMES[result.actor]} defends and will block the next attack."
    if isinstance(result, WindUpResult):
        return (
            f"!! {NAMES[result.actor]} is winding up a HEAVY ATTACK. It strikes on its "
            f"next turn for {result.damage} damage unless you defend."
        )
    target = Side.ENEMY if result.attacker is Side.PLAYER else Side.PLAYER
    verb = "unleashes a HEAVY ATTACK on" if result.heavy else "attacks"
    if result.blocked:
        hit = f"{NAMES[result.attacker]} {verb} {NAMES[target]}, but the attack is blocked!"
    else:
        hit = f"{NAMES[result.attacker]} {verb} {NAMES[target]} for {result.damage} damage."
    return f"{hit} Player HP {encounter.player.health} | Enemy HP {encounter.enemy.health}"


def _ask(read: Read, write: Write, prompt: str, choices: dict[str, object]) -> object | None:
    """Prompt until the answer is one of ``choices``; ``None`` on end of input."""
    while True:
        try:
            answer = read(prompt).strip().lower()
        except EOFError:
            return None
        if answer in choices:
            return choices[answer]
        write(f"Unrecognized choice {answer!r}. Options: {', '.join(sorted(set(choices)))}.")


TURN_CHOICES = {
    "a": Action.ATTACK,
    "attack": Action.ATTACK,
    "d": Action.DEFEND,
    "defend": Action.DEFEND,
    "q": "quit",
    "quit": "quit",
}
AGAIN_CHOICES = {"y": "yes", "yes": "yes", "n": "no", "no": "no", "q": "no", "quit": "no"}


def enemy_action(enemy_turn: int, encounter: Encounter, heavy: bool) -> Action:
    """The enemy's scripted action for its ``enemy_turn``-th turn (1-based)."""
    if encounter.enemy.winding_up:
        return Action.ATTACK  # the announced heavy attack
    if heavy and enemy_turn % HEAVY_CYCLE == 2:
        return Action.WIND_UP
    return Action.ATTACK


def play_encounter(
    read: Read, write: Write, encounter: Encounter, heavy: bool = False
) -> str | None:
    """Play one encounter. Returns ``WON``, ``LOST``, or ``None`` if the player quit."""
    write(describe_character(Side.PLAYER, encounter.player))
    write(describe_character(Side.ENEMY, encounter.enemy))

    enemy_turns = 0
    while not encounter.finished:
        side = encounter.current_turn
        warning = " (HEAVY ATTACK INCOMING)" if encounter.enemy.winding_up else ""
        write(f"-- {NAMES[side]}'s turn --{warning if side is Side.PLAYER else ''}")
        if side is Side.ENEMY:
            enemy_turns += 1
            action = enemy_action(enemy_turns, encounter, heavy)
        else:
            action = _ask(read, write, "[a]ttack, [d]efend or [q]uit > ", TURN_CHOICES)
            if not isinstance(action, Action):
                return None
        result = encounter.perform(side, action)
        write(describe_result(result, encounter))

    outcome = LOST if encounter.player.defeated else WON
    write("Victory! The enemy is defeated." if outcome == WON else "Defeat. You have fallen.")
    return outcome


def run(
    read: Read = input,
    write: Write = print,
    make_player: Callable[[], Character] = default_player,
    make_enemy: Callable[[], Character] = default_enemy,
    heavy: bool = False,
) -> list[str]:
    """Run encounters until the player quits. Returns each finished outcome."""
    outcomes: list[str] = []
    write("MUDDY-FATE combat prototype (provisional rules).")
    if heavy:
        write("EXPERIMENTAL: the enemy sometimes telegraphs a heavy attack.")
    while True:
        write(f"\n=== Encounter {len(outcomes) + 1} ===")
        outcome = play_encounter(read, write, Encounter(make_player(), make_enemy()), heavy)
        if outcome is None:
            break
        outcomes.append(outcome)
        if _ask(read, write, "Fight again? [y]es / [n]o > ", AGAIN_CHOICES) != "yes":
            break
    wins = outcomes.count(WON)
    write(f"Goodbye. Encounters finished: {len(outcomes)} (won {wins}, lost {len(outcomes) - wins}).")
    return outcomes


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m game.sim")
    parser.add_argument(
        "--heavy",
        action="store_true",
        help="EXPERIMENTAL: enemy telegraphs a heavy attack every third turn",
    )
    args = parser.parse_args(argv)
    try:
        run(heavy=args.heavy)
    except KeyboardInterrupt:
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
