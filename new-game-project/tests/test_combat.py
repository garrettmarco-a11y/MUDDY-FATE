from dataclasses import fields

import pytest

from game.combat import (
    Action,
    AttackResult,
    Character,
    CombatError,
    Encounter,
    Side,
    Traits,
    calculate_damage,
)

TRAIT_NAMES = ["puissant", "alacrity", "measure", "aptitude", "acumen", "glamour"]


def traits(puissant=0, **overrides):
    # Small explicit test values; only Puissant matters for combat.
    values = dict.fromkeys(TRAIT_NAMES, 0)
    values.update(puissant=puissant, **overrides)
    return Traits(**values)


def character(puissant=0, health=10, **overrides):
    return Character(traits(puissant, **overrides), health=health)


def encounter(player_puissant=0, player_health=10, enemy_puissant=0, enemy_health=10):
    return Encounter(
        character(player_puissant, player_health),
        character(enemy_puissant, enemy_health),
    )


def take_turn_to(enc, side):
    # The player always acts first; reach the enemy's turn with one player hit.
    if side is Side.ENEMY:
        enc.perform(Side.PLAYER, Action.ATTACK)
    assert enc.current_turn is side


def test_example_encounter():
    # Minimal usage: create an encounter, attack both ways, inspect results.
    enc = encounter(player_puissant=3, player_health=10, enemy_puissant=2, enemy_health=5)

    assert enc.current_turn is Side.PLAYER
    player_hit = enc.perform(Side.PLAYER, Action.ATTACK)
    assert enc.current_turn is Side.ENEMY
    enemy_hit = enc.perform(Side.ENEMY, Action.ATTACK)

    assert player_hit == AttackResult(
        attacker=Side.PLAYER, damage=3, health_before=5, health_after=2, defeated=False
    )
    assert enemy_hit == AttackResult(
        attacker=Side.ENEMY, damage=2, health_before=10, health_after=8, defeated=False
    )
    assert (enc.player.health, enc.enemy.health) == (8, 2)
    assert enc.current_turn is Side.PLAYER
    assert not enc.finished


# --- shared trait model --------------------------------------------------


def test_traits_have_exactly_the_six_named_fields():
    assert [f.name for f in fields(Traits)] == TRAIT_NAMES


def test_player_and_enemy_use_the_same_model_with_all_traits():
    values = dict(puissant=4, alacrity=1, measure=2, aptitude=3, acumen=5, glamour=6)
    player = Character(Traits(**values), health=10)
    enemy = Character(Traits(**values), health=7)

    assert type(player) is type(enemy) is Character
    for name, value in values.items():
        assert getattr(player.traits, name) == value
        assert getattr(enemy.traits, name) == value


def test_all_traits_are_required():
    with pytest.raises(TypeError):
        Traits(puissant=1)


def test_zero_traits_are_allowed():
    assert traits() == Traits(**dict.fromkeys(TRAIT_NAMES, 0))


def test_non_puissant_traits_do_not_affect_damage():
    plain = encounter(player_puissant=3, enemy_health=10)
    boosted = Encounter(
        character(3, alacrity=9, measure=9, aptitude=9, acumen=9, glamour=9),
        character(0, health=10, alacrity=9, measure=9, aptitude=9, acumen=9, glamour=9),
    )

    assert plain.perform(Side.PLAYER, Action.ATTACK) == boosted.perform(
        Side.PLAYER, Action.ATTACK
    )


# --- damage rule ---------------------------------------------------------


@pytest.mark.parametrize("puissant, expected", [(1, 1), (2, 2), (5, 5), (12, 12)])
def test_damage_equals_puissant(puissant, expected):
    assert calculate_damage(puissant) == expected


def test_minimum_damage_is_one():
    assert calculate_damage(0) == 1


@pytest.mark.parametrize("value", [-1, -3])
def test_calculate_damage_rejects_negative_puissant(value):
    with pytest.raises(ValueError):
        calculate_damage(value)


@pytest.mark.parametrize("value", [3.5, "3", None, True])
def test_calculate_damage_rejects_non_int_puissant(value):
    with pytest.raises(TypeError):
        calculate_damage(value)


@pytest.mark.parametrize("side", [Side.PLAYER, Side.ENEMY])
def test_zero_puissant_attack_still_deals_one_damage(side):
    enc = encounter(player_health=3, enemy_health=3)
    take_turn_to(enc, side)

    result = enc.perform(side, Action.ATTACK)

    assert result.damage == 1
    assert result.health_after == 2


# --- attacks in both directions -----------------------------------------


def test_player_attack_reduces_enemy_health_only():
    enc = encounter(player_puissant=4, player_health=10, enemy_health=10)

    result = enc.perform(Side.PLAYER, Action.ATTACK)

    assert result.attacker is Side.PLAYER
    assert (result.health_before, result.health_after) == (10, 6)
    assert not result.defeated
    assert (enc.player.health, enc.enemy.health) == (10, 6)


def test_enemy_attack_reduces_player_health_only():
    enc = encounter(player_health=10, enemy_puissant=4, enemy_health=10)
    take_turn_to(enc, Side.ENEMY)  # player (Puissant 0) deals 1: enemy 10 -> 9

    result = enc.perform(Side.ENEMY, Action.ATTACK)

    assert result.attacker is Side.ENEMY
    assert (result.health_before, result.health_after) == (10, 6)
    assert not result.defeated
    assert (enc.player.health, enc.enemy.health) == (6, 9)


@pytest.mark.parametrize("side", [Side.PLAYER, Side.ENEMY])
def test_lethal_attack_reaches_exactly_zero(side):
    player_puissant = 5 if side is Side.PLAYER else 0
    enc = encounter(player_puissant, player_health=5, enemy_puissant=5, enemy_health=5)
    take_turn_to(enc, side)

    result = enc.perform(side, Action.ATTACK)

    assert result.damage == 5
    assert result.health_after == 0
    assert result.defeated
    assert enc.finished


@pytest.mark.parametrize("side", [Side.PLAYER, Side.ENEMY])
def test_overkill_clamps_health_and_reports_applied_damage(side):
    player_puissant = 9 if side is Side.PLAYER else 0
    enc = encounter(player_puissant, player_health=3, enemy_puissant=9, enemy_health=4)
    take_turn_to(enc, side)

    result = enc.perform(side, Action.ATTACK)

    # Reports health actually removed, not the calculated 9.
    expected = 4 if side is Side.PLAYER else 3
    assert result.damage == expected
    assert result.health_after == 0
    target = enc.enemy if side is Side.PLAYER else enc.player
    assert target.health == 0
    assert target.defeated


def test_alternating_attacks_until_defeat():
    enc = encounter(player_puissant=3, player_health=5, enemy_puissant=2, enemy_health=7)

    log = []
    for side in [Side.PLAYER, Side.ENEMY, Side.PLAYER, Side.ENEMY, Side.PLAYER]:
        result = enc.perform(side, Action.ATTACK)
        log.append((side, result.damage, result.health_after))

    assert log == [
        (Side.PLAYER, 3, 4),
        (Side.ENEMY, 2, 3),
        (Side.PLAYER, 3, 1),
        (Side.ENEMY, 2, 1),
        (Side.PLAYER, 1, 0),
    ]
    assert enc.enemy.defeated
    assert not enc.player.defeated


# --- turn order --------------------------------------------------------


def test_new_encounter_starts_on_player_turn():
    enc = encounter()

    assert enc.current_turn is Side.PLAYER
    assert not enc.finished


def test_turns_alternate_after_each_nonlethal_attack():
    enc = encounter(player_puissant=1, enemy_puissant=1)

    turns = [enc.current_turn]
    for _ in range(4):
        enc.perform(enc.current_turn, Action.ATTACK)
        turns.append(enc.current_turn)

    assert turns == [Side.PLAYER, Side.ENEMY, Side.PLAYER, Side.ENEMY, Side.PLAYER]


@pytest.mark.parametrize("turn, intruder", [(Side.PLAYER, Side.ENEMY), (Side.ENEMY, Side.PLAYER)])
def test_out_of_turn_attack_is_rejected_without_change(turn, intruder):
    enc = encounter(player_puissant=2, enemy_puissant=2)
    take_turn_to(enc, turn)
    state = (enc.player, enc.enemy)

    with pytest.raises(CombatError, match=f"not {intruder.value}'s turn"):
        enc.perform(intruder, Action.ATTACK)

    assert (enc.player, enc.enemy) == state
    assert enc.current_turn is turn
    assert not enc.finished


@pytest.mark.parametrize("bad_actor", ["player", None])
def test_rejected_input_does_not_advance_turn(bad_actor):
    enc = encounter(player_puissant=2)

    with pytest.raises(CombatError):
        enc.perform(bad_actor, Action.ATTACK)
    with pytest.raises(CombatError):
        enc.perform(Side.PLAYER, "attack")

    assert enc.current_turn is Side.PLAYER


# --- encounter end -------------------------------------------------------


@pytest.mark.parametrize("winner, loser", [(Side.PLAYER, Side.ENEMY), (Side.ENEMY, Side.PLAYER)])
def test_lethal_attack_finishes_encounter_with_no_next_turn(winner, loser):
    player_puissant = 5 if winner is Side.PLAYER else 0
    enc = encounter(player_puissant, player_health=5, enemy_puissant=5, enemy_health=5)
    take_turn_to(enc, winner)

    enc.perform(winner, Action.ATTACK)

    assert enc.finished
    assert enc.current_turn is None
    defeated = enc.enemy if loser is Side.ENEMY else enc.player
    assert defeated.defeated


@pytest.mark.parametrize("winner, loser", [(Side.PLAYER, Side.ENEMY), (Side.ENEMY, Side.PLAYER)])
def test_no_action_after_encounter_is_finished(winner, loser):
    player_puissant = 5 if winner is Side.PLAYER else 0
    enc = encounter(player_puissant, player_health=5, enemy_puissant=5, enemy_health=5)
    take_turn_to(enc, winner)
    enc.perform(winner, Action.ATTACK)
    state = (enc.player, enc.enemy)

    for side in (winner, loser):
        with pytest.raises(CombatError, match="encounter is finished"):
            enc.perform(side, Action.ATTACK)

    assert (enc.player, enc.enemy) == state
    assert enc.finished
    assert enc.current_turn is None


def test_full_exchange_to_enemy_victory():
    enc = encounter(player_puissant=1, player_health=4, enemy_puissant=2, enemy_health=10)

    log = []
    while not enc.finished:
        side = enc.current_turn
        result = enc.perform(side, Action.ATTACK)
        log.append((side, result.health_after))

    assert log == [
        (Side.PLAYER, 9),
        (Side.ENEMY, 2),
        (Side.PLAYER, 8),
        (Side.ENEMY, 0),
    ]
    assert enc.player.defeated
    assert enc.current_turn is None


# --- determinism ---------------------------------------------------------


def test_equivalent_encounters_produce_identical_results():
    def run():
        enc = encounter(player_puissant=4, player_health=9, enemy_puissant=3, enemy_health=10)
        sides = [Side.PLAYER, Side.ENEMY, Side.PLAYER, Side.ENEMY]
        return [enc.perform(side, Action.ATTACK) for side in sides]

    assert run() == run()


# --- invalid inputs and states ------------------------------------------


@pytest.mark.parametrize("name", TRAIT_NAMES)
@pytest.mark.parametrize("value", [-1, -10])
def test_negative_trait_is_rejected(name, value):
    with pytest.raises(ValueError, match=name):
        traits(**{name: value})


@pytest.mark.parametrize("name", TRAIT_NAMES)
@pytest.mark.parametrize("value", [1.5, "3", None, True])
def test_non_int_trait_is_rejected(name, value):
    with pytest.raises(TypeError, match=name):
        traits(**{name: value})


def test_negative_health_is_rejected():
    with pytest.raises(ValueError):
        character(health=-1)


@pytest.mark.parametrize("value", [2.0, "5", None, False])
def test_non_int_health_is_rejected(value):
    with pytest.raises(TypeError):
        character(health=value)


def test_character_requires_traits_object():
    with pytest.raises(TypeError):
        Character(traits={"puissant": 1}, health=1)


def test_zero_health_character_is_defeated():
    assert character(health=0).defeated
    assert not character(health=1).defeated


@pytest.mark.parametrize("player_health, enemy_health", [(0, 5), (5, 0), (0, 0)])
def test_encounter_cannot_start_with_defeated_character(player_health, enemy_health):
    with pytest.raises(CombatError):
        Encounter(character(health=player_health), character(health=enemy_health))


def test_encounter_requires_characters():
    with pytest.raises(TypeError):
        Encounter(object(), character())
    with pytest.raises(TypeError):
        Encounter(character(), object())


@pytest.mark.parametrize("action", ["attack", None, 1])
def test_unsupported_action_is_rejected_without_change(action):
    enc = encounter(player_puissant=2, enemy_health=5)

    with pytest.raises(CombatError, match="unsupported action"):
        enc.perform(Side.PLAYER, action)

    assert enc.enemy.health == 5


@pytest.mark.parametrize("actor", ["player", None, 0])
def test_unsupported_side_is_rejected_without_change(actor):
    enc = encounter(player_puissant=2, enemy_health=5)

    with pytest.raises(CombatError, match="unsupported side"):
        enc.perform(actor, Action.ATTACK)

    assert (enc.player.health, enc.enemy.health) == (10, 5)


def test_traits_and_characters_are_immutable():
    c = character(puissant=1, health=1)
    with pytest.raises(AttributeError):
        c.health = -5
    with pytest.raises(AttributeError):
        c.traits.puissant = 99


def test_attack_does_not_mutate_original_characters():
    player, enemy = character(3, health=10), character(3, health=10)
    enc = Encounter(player, enemy)

    enc.perform(Side.PLAYER, Action.ATTACK)
    enc.perform(Side.ENEMY, Action.ATTACK)

    assert (player.health, enemy.health) == (10, 10)
    assert (enc.player.health, enc.enemy.health) == (7, 7)
