"""First combat slice: one player, one enemy, one basic attack.

Status: PROVISIONAL. This is a minimal, deterministic starting point, not the
final combat system or balance.

Damage rule (PROVISIONAL):

    damage = max(1, puissant - defense)

Enemy defense is fixed at ``ENEMY_DEFENSE = 0`` for this encounter, so the
effective rule is ``max(1, puissant)``. Only Puissant (Strength) participates
in combat resolution; no other trait has a combat function yet.

``AttackResult.damage`` is the health actually removed, so an overkill hit
reports only the enemy's remaining health.

Error behavior:

- Invalid construction values or ``calculate_damage`` arguments (wrong type,
  out of range) raise ``TypeError`` or ``ValueError``.
- Unsupported actions, starting an encounter against an already defeated
  enemy, and attacking a defeated enemy raise ``CombatError``. A rejected
  action never changes encounter state.

Example::

    encounter = Encounter(Player(puissant=3), Enemy(health=5))
    result = encounter.perform(Action.ATTACK)
    result.damage, result.health_after, result.defeated  # (3, 2, False)
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

# PROVISIONAL: fixed for the first encounter; not a defense system.
ENEMY_DEFENSE = 0


class CombatError(Exception):
    """An action that is not valid in the current combat state."""


class Action(Enum):
    ATTACK = "attack"


def _require_int(name: str, value: object, minimum: int) -> None:
    # bool is a subclass of int; reject it so True/False are not traits.
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


@dataclass(frozen=True)
class Player:
    puissant: int

    def __post_init__(self) -> None:
        _require_int("puissant", self.puissant, minimum=0)


@dataclass(frozen=True)
class Enemy:
    health: int

    def __post_init__(self) -> None:
        _require_int("health", self.health, minimum=0)

    @property
    def defeated(self) -> bool:
        return self.health == 0


@dataclass(frozen=True)
class AttackResult:
    # Health actually removed; less than the calculated damage on overkill.
    damage: int
    health_before: int
    health_after: int
    defeated: bool


def calculate_damage(puissant: int) -> int:
    """PROVISIONAL damage rule: ``max(1, puissant - ENEMY_DEFENSE)``.

    Validates ``puissant`` with the same rules as ``Player``.
    """
    _require_int("puissant", puissant, minimum=0)
    return max(1, puissant - ENEMY_DEFENSE)


class Encounter:
    """A single player versus a single enemy. Only the player acts."""

    def __init__(self, player: Player, enemy: Enemy) -> None:
        if not isinstance(player, Player):
            raise TypeError("player must be a Player")
        if not isinstance(enemy, Enemy):
            raise TypeError("enemy must be an Enemy")
        if enemy.defeated:
            raise CombatError("cannot start an encounter against a defeated enemy")
        self.player = player
        self.enemy = enemy

    def perform(self, action: Action) -> AttackResult:
        if action is not Action.ATTACK:
            raise CombatError(f"unsupported action: {action!r}")
        return self._attack()

    def _attack(self) -> AttackResult:
        if self.enemy.defeated:
            raise CombatError("enemy is already defeated")
        before = self.enemy.health
        after = max(0, before - calculate_damage(self.player.puissant))
        self.enemy = replace(self.enemy, health=after)
        return AttackResult(
            damage=before - after,
            health_before=before,
            health_after=self.enemy.health,
            defeated=self.enemy.defeated,
        )
