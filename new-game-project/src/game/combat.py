"""Turn-based combat: one player and one enemy, alternating attacks or defends.

Status: PROVISIONAL. This is a minimal, deterministic starting point, not the
final combat system or balance.

Players and enemies share one model: a ``Character`` with all six traits and
integer health. Which side a character is on is decided by its position in
the ``Encounter``, not by its type.

Damage rule (PROVISIONAL):

    damage = max(1, puissant - defense)

Defense is fixed at ``DEFENSE = 0``, so the effective rule is
``max(1, puissant)``. Only Puissant (Strength) affects combat. The other five
traits are stored on every character but have no mechanical effect yet.

Turn order: the player acts first, then turns alternate after each attack. The
caller chooses when each side acts; nothing acts automatically. When an attack
reduces either character to zero health the encounter is finished and
``current_turn`` is ``None``: there is no next turn.

``AttackResult.damage`` is the health actually removed, so an overkill hit
reports only the target's remaining health.

Defend rule (PROVISIONAL, approved for this prototype only):

- ``Action.DEFEND`` uses the actor's turn and sets ``Character.defending``.
- The next attack against a defending character is blocked completely: it
  applies 0 damage, even if it would have been lethal, and
  ``AttackResult.blocked`` is ``True``. That attack consumes the block.
- Blocks do not stack; defending while already defending leaves one block.
- The block belongs to the defended character, not to a particular attacker,
  and stays until an attack consumes it or the encounter ends.

Telegraphed heavy attack (EXPERIMENTAL playtest; may be removed):

- ``Action.WIND_UP`` uses the actor's turn, deals no damage, and sets
  ``Character.winding_up`` so the opponent is warned.
- A winding-up character's next action must be ``ATTACK``; any other action
  is rejected. That attack is heavy: ``calculate_heavy_damage(puissant)``,
  which is the normal damage plus ``HEAVY_BONUS``. ``AttackResult.heavy`` is
  ``True``, and the wind-up is used up, so one wind-up yields one heavy attack.
- Defend blocks a heavy attack like any other attack.

Error behavior:

- Invalid construction values or ``calculate_damage`` arguments (wrong type,
  out of range) raise ``TypeError`` or ``ValueError``.
- Unsupported actions or sides, starting an encounter when either character is
  already defeated, acting out of turn, and acting after the encounter is
  finished raise ``CombatError``. A rejected action never changes encounter
  state, including whose turn it is.

Example::

    player = Character(Traits(puissant=3, alacrity=0, measure=0,
                              aptitude=0, acumen=0, glamour=0), health=10)
    enemy = Character(Traits(puissant=2, alacrity=0, measure=0,
                             aptitude=0, acumen=0, glamour=0), health=5)
    encounter = Encounter(player, enemy)
    encounter.current_turn                                      # Side.PLAYER
    encounter.perform(Side.PLAYER, Action.ATTACK).health_after  # enemy: 2
    encounter.current_turn                                      # Side.ENEMY
    encounter.perform(Side.ENEMY, Action.ATTACK).health_after   # player: 8
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum

# PROVISIONAL: fixed for every attack; not a defense system.
DEFENSE = 0

# EXPERIMENTAL: flat extra damage for a telegraphed heavy attack. Not balanced.
HEAVY_BONUS = 3


class CombatError(Exception):
    """An action that is not valid in the current combat state."""


class Action(Enum):
    ATTACK = "attack"
    DEFEND = "defend"
    WIND_UP = "wind_up"  # EXPERIMENTAL


class Side(Enum):
    PLAYER = "player"
    ENEMY = "enemy"


def _require_int(name: str, value: object, minimum: int) -> None:
    # bool is a subclass of int; reject it so True/False are not values.
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


@dataclass(frozen=True)
class Traits:
    """The six character traits. No scale or upper limit is defined yet."""

    puissant: int  # Strength; the only trait used in combat so far
    alacrity: int  # Dexterity
    measure: int  # Constitution
    aptitude: int  # Intelligence
    acumen: int  # Wisdom
    glamour: int  # Charisma

    def __post_init__(self) -> None:
        for field in fields(self):
            _require_int(field.name, getattr(self, field.name), minimum=0)


@dataclass(frozen=True)
class Character:
    """Shared model for players and enemies."""

    traits: Traits
    health: int
    # PROVISIONAL: one-use block against the next incoming attack.
    defending: bool = False
    # EXPERIMENTAL: announced a heavy attack that lands on its next action.
    winding_up: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.traits, Traits):
            raise TypeError("traits must be a Traits")
        _require_int("health", self.health, minimum=0)
        if not isinstance(self.defending, bool):
            raise TypeError("defending must be a bool")
        if not isinstance(self.winding_up, bool):
            raise TypeError("winding_up must be a bool")

    @property
    def defeated(self) -> bool:
        return self.health == 0


@dataclass(frozen=True)
class AttackResult:
    attacker: Side
    # Health actually removed; less than the calculated damage on overkill.
    damage: int
    health_before: int  # target's
    health_after: int  # target's
    defeated: bool  # whether the target is now defeated
    blocked: bool = False  # the target's defend absorbed this attack
    heavy: bool = False  # EXPERIMENTAL: this was a telegraphed heavy attack


@dataclass(frozen=True)
class DefendResult:
    actor: Side


@dataclass(frozen=True)
class WindUpResult:
    """EXPERIMENTAL: ``actor`` announced a heavy attack for ``damage``."""

    actor: Side
    damage: int  # what the heavy attack will deal if not blocked


def calculate_damage(puissant: int) -> int:
    """PROVISIONAL damage rule: ``max(1, puissant - DEFENSE)``.

    Validates ``puissant`` with the same rules as ``Traits``.
    """
    _require_int("puissant", puissant, minimum=0)
    return max(1, puissant - DEFENSE)


def calculate_heavy_damage(puissant: int) -> int:
    """EXPERIMENTAL heavy attack damage: normal damage plus ``HEAVY_BONUS``."""
    return calculate_damage(puissant) + HEAVY_BONUS


class Encounter:
    """A single player versus a single enemy, taking turns.

    The player acts first. The caller requests each action explicitly for the
    side whose turn it is; the encounter only enforces the order.
    """

    def __init__(self, player: Character, enemy: Character) -> None:
        if not isinstance(player, Character):
            raise TypeError("player must be a Character")
        if not isinstance(enemy, Character):
            raise TypeError("enemy must be a Character")
        if player.defeated or enemy.defeated:
            raise CombatError("cannot start an encounter with a defeated character")
        self.player = player
        self.enemy = enemy
        self._turn = Side.PLAYER

    @property
    def finished(self) -> bool:
        return self.player.defeated or self.enemy.defeated

    @property
    def current_turn(self) -> Side | None:
        """The side that acts next, or ``None`` once the encounter is finished."""
        return None if self.finished else self._turn

    def perform(
        self, actor: Side, action: Action
    ) -> AttackResult | DefendResult | WindUpResult:
        if not isinstance(actor, Side):
            raise CombatError(f"unsupported side: {actor!r}")
        if not isinstance(action, Action):
            raise CombatError(f"unsupported action: {action!r}")
        if self.finished:
            raise CombatError("encounter is finished")
        if actor is not self._turn:
            raise CombatError(f"not {actor.value}'s turn; {self._turn.value} acts next")
        if action is not Action.ATTACK and self._character(actor).winding_up:
            raise CombatError(f"{actor.value} is winding up a heavy attack and must attack")
        if action is Action.DEFEND:
            result = self._defend(actor)
        elif action is Action.WIND_UP:
            result = self._wind_up(actor)
        else:
            result = self._attack(actor)
        if not self.finished:
            self._turn = Side.ENEMY if actor is Side.PLAYER else Side.PLAYER
        return result

    def _character(self, side: Side) -> Character:
        return self.player if side is Side.PLAYER else self.enemy

    def _wind_up(self, actor: Side) -> WindUpResult:
        if actor is Side.PLAYER:
            self.player = replace(self.player, winding_up=True)
        else:
            self.enemy = replace(self.enemy, winding_up=True)
        damage = calculate_heavy_damage(self._character(actor).traits.puissant)
        return WindUpResult(actor=actor, damage=damage)

    def _defend(self, actor: Side) -> DefendResult:
        if actor is Side.PLAYER:
            self.player = replace(self.player, defending=True)
        else:
            self.enemy = replace(self.enemy, defending=True)
        return DefendResult(actor=actor)

    def _attack(self, actor: Side) -> AttackResult:
        if actor is Side.PLAYER:
            attacker, target = self.player, self.enemy
        else:
            attacker, target = self.enemy, self.player

        heavy = attacker.winding_up
        damage_rule = calculate_heavy_damage if heavy else calculate_damage
        before = target.health
        blocked = target.defending
        if blocked:
            after = before
        else:
            after = max(0, before - damage_rule(attacker.traits.puissant))
        target = replace(target, health=after, defending=False)
        attacker = replace(attacker, winding_up=False)
        if actor is Side.PLAYER:
            self.player, self.enemy = attacker, target
        else:
            self.enemy, self.player = attacker, target
        return AttackResult(
            attacker=actor,
            damage=before - after,
            health_before=before,
            health_after=after,
            defeated=target.defeated,
            blocked=blocked,
            heavy=heavy,
        )
