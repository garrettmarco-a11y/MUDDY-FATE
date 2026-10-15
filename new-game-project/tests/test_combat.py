import pytest

from game.combat import (
    Action,
    AttackResult,
    CombatError,
    Encounter,
    Enemy,
    Player,
    calculate_damage,
)


def test_example_encounter():
    # Minimal usage: create an encounter, attack, inspect the result.
    encounter = Encounter(Player(puissant=3), Enemy(health=5))

    result = encounter.perform(Action.ATTACK)

    assert result == AttackResult(damage=3, health_before=5, health_after=2, defeated=False)
    assert encounter.enemy.health == 2


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


def test_zero_puissant_attack_still_deals_one_damage():
    encounter = Encounter(Player(puissant=0), Enemy(health=3))

    result = encounter.perform(Action.ATTACK)

    assert result.damage == 1
    assert result.health_after == 2


# --- health and defeat ---------------------------------------------------


def test_nonlethal_attack_reduces_health():
    encounter = Encounter(Player(puissant=4), Enemy(health=10))

    result = encounter.perform(Action.ATTACK)

    assert (result.health_before, result.health_after) == (10, 6)
    assert not result.defeated
    assert not encounter.enemy.defeated


def test_lethal_attack_reaches_exactly_zero():
    encounter = Encounter(Player(puissant=5), Enemy(health=5))

    result = encounter.perform(Action.ATTACK)

    assert result.health_after == 0
    assert result.defeated
    assert encounter.enemy.defeated


def test_overkill_clamps_health_at_zero():
    encounter = Encounter(Player(puissant=9), Enemy(health=3))

    result = encounter.perform(Action.ATTACK)

    # Reports health actually removed, not the calculated 9.
    assert result.damage == 3
    assert result.health_after == 0
    assert encounter.enemy.health == 0
    assert result.defeated


def test_repeated_attacks_until_defeat():
    encounter = Encounter(Player(puissant=3), Enemy(health=7))

    healths = [encounter.perform(Action.ATTACK).health_after for _ in range(3)]

    assert healths == [4, 1, 0]
    assert encounter.enemy.defeated


def test_attack_against_defeated_enemy_is_rejected_without_change():
    encounter = Encounter(Player(puissant=5), Enemy(health=5))
    encounter.perform(Action.ATTACK)
    enemy_before = encounter.enemy

    with pytest.raises(CombatError, match="already defeated"):
        encounter.perform(Action.ATTACK)

    assert encounter.enemy is enemy_before
    assert encounter.enemy.health == 0


# --- determinism ---------------------------------------------------------


def test_equivalent_encounters_produce_identical_results():
    def run():
        encounter = Encounter(Player(puissant=4), Enemy(health=10))
        return [encounter.perform(Action.ATTACK) for _ in range(3)]

    assert run() == run()


# --- invalid inputs and states ------------------------------------------


@pytest.mark.parametrize("value", [-1, -10])
def test_negative_puissant_is_rejected(value):
    with pytest.raises(ValueError):
        Player(puissant=value)


@pytest.mark.parametrize("value", [1.5, "3", None, True])
def test_non_int_puissant_is_rejected(value):
    with pytest.raises(TypeError):
        Player(puissant=value)


def test_negative_health_is_rejected():
    with pytest.raises(ValueError):
        Enemy(health=-1)


@pytest.mark.parametrize("value", [2.0, "5", None, False])
def test_non_int_health_is_rejected(value):
    with pytest.raises(TypeError):
        Enemy(health=value)


def test_encounter_cannot_start_against_defeated_enemy():
    with pytest.raises(CombatError):
        Encounter(Player(puissant=1), Enemy(health=0))


def test_encounter_requires_player_and_enemy_types():
    with pytest.raises(TypeError):
        Encounter(object(), Enemy(health=1))
    with pytest.raises(TypeError):
        Encounter(Player(puissant=1), object())


@pytest.mark.parametrize("action", ["attack", None, 1])
def test_unsupported_action_is_rejected_without_change(action):
    encounter = Encounter(Player(puissant=2), Enemy(health=5))

    with pytest.raises(CombatError, match="unsupported action"):
        encounter.perform(action)

    assert encounter.enemy.health == 5


def test_player_and_enemy_are_immutable():
    player, enemy = Player(puissant=1), Enemy(health=1)
    with pytest.raises(AttributeError):
        player.puissant = 99
    with pytest.raises(AttributeError):
        enemy.health = -5
