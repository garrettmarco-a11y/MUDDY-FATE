"""EXPERIMENTAL telegraphed heavy attack. Delete with the experiment if removed."""

import subprocess
import sys

import pytest

from game.combat import (
    HEAVY_BONUS,
    Action,
    Character,
    CombatError,
    Encounter,
    Side,
    Traits,
    WindUpResult,
    calculate_damage,
    calculate_heavy_damage,
)
from game.sim import LOST, WON, enemy_action, run

from test_sim import Script


def traits(puissant=0):
    return Traits(puissant=puissant, alacrity=0, measure=0, aptitude=0, acumen=0, glamour=0)


def character(puissant=0, health=10, **flags):
    return Character(traits(puissant), health=health, **flags)


def maker(puissant, health):
    return lambda: character(puissant, health)


def wound_up(player_puissant=1, player_health=10, enemy_puissant=2, enemy_health=10):
    """Encounter where the enemy has just wound up; it is the player's turn."""
    enc = Encounter(character(player_puissant, player_health), character(enemy_puissant, enemy_health))
    enc.perform(Side.PLAYER, Action.ATTACK)
    enc.perform(Side.ENEMY, Action.WIND_UP)
    return enc


# --- engine --------------------------------------------------------------


@pytest.mark.parametrize("puissant", [0, 1, 2, 5])
def test_heavy_damage_is_normal_damage_plus_fixed_bonus(puissant):
    assert calculate_heavy_damage(puissant) == calculate_damage(puissant) + HEAVY_BONUS


@pytest.mark.parametrize("value, error", [(-1, ValueError), (2.5, TypeError), (True, TypeError)])
def test_heavy_damage_validates_input(value, error):
    with pytest.raises(error):
        calculate_heavy_damage(value)


def test_wind_up_uses_turn_deals_no_damage_and_announces_damage():
    enc = Encounter(character(1), character(2))
    enc.perform(Side.PLAYER, Action.ATTACK)

    result = enc.perform(Side.ENEMY, Action.WIND_UP)

    assert result == WindUpResult(actor=Side.ENEMY, damage=2 + HEAVY_BONUS)
    assert enc.enemy.winding_up
    assert enc.player.health == 10
    assert enc.current_turn is Side.PLAYER  # the player can respond first


def test_heavy_attack_lands_when_player_attacks_instead():
    enc = wound_up()
    enc.perform(Side.PLAYER, Action.ATTACK)

    result = enc.perform(Side.ENEMY, Action.ATTACK)

    assert result.heavy and not result.blocked
    assert result.damage == 2 + HEAVY_BONUS
    assert enc.player.health == 10 - (2 + HEAVY_BONUS)
    assert not enc.enemy.winding_up


def test_defend_blocks_heavy_attack_and_consumes_block():
    enc = wound_up()
    enc.perform(Side.PLAYER, Action.DEFEND)

    result = enc.perform(Side.ENEMY, Action.ATTACK)

    assert result.heavy and result.blocked
    assert result.damage == 0
    assert enc.player.health == 10
    assert not enc.player.defending
    assert not enc.enemy.winding_up


def test_one_wind_up_yields_exactly_one_heavy_attack():
    enc = wound_up()
    enc.perform(Side.PLAYER, Action.ATTACK)
    first = enc.perform(Side.ENEMY, Action.ATTACK)
    enc.perform(Side.PLAYER, Action.ATTACK)
    second = enc.perform(Side.ENEMY, Action.ATTACK)

    assert first.heavy and first.damage == 5
    assert not second.heavy and second.damage == 2


def test_wound_up_character_must_attack_next():
    enc = wound_up()
    enc.perform(Side.PLAYER, Action.ATTACK)
    state = (enc.player, enc.enemy)

    for action in (Action.DEFEND, Action.WIND_UP):
        with pytest.raises(CombatError, match="must attack"):
            enc.perform(Side.ENEMY, action)

    assert (enc.player, enc.enemy) == state
    assert enc.current_turn is Side.ENEMY


def test_wind_up_out_of_turn_is_rejected_without_change():
    enc = Encounter(character(1), character(2))
    state = (enc.player, enc.enemy)

    with pytest.raises(CombatError, match="not enemy's turn"):
        enc.perform(Side.ENEMY, Action.WIND_UP)

    assert (enc.player, enc.enemy) == state
    assert not enc.enemy.winding_up
    assert enc.current_turn is Side.PLAYER


def test_lethal_heavy_attack_finishes_encounter():
    enc = wound_up(player_health=5)
    enc.perform(Side.PLAYER, Action.ATTACK)

    result = enc.perform(Side.ENEMY, Action.ATTACK)

    assert result.heavy and result.defeated
    assert result.damage == 5
    assert enc.finished and enc.current_turn is None


def test_heavy_overkill_reports_applied_damage():
    enc = wound_up(player_health=3)
    enc.perform(Side.PLAYER, Action.ATTACK)

    result = enc.perform(Side.ENEMY, Action.ATTACK)

    assert result.damage == 3
    assert enc.player.health == 0


def test_killing_a_wound_up_enemy_ends_encounter_without_heavy_attack():
    enc = wound_up(player_puissant=5, enemy_health=6)  # enemy at 1 HP after first hit

    enc.perform(Side.PLAYER, Action.ATTACK)

    assert enc.finished
    assert enc.player.health == 10
    with pytest.raises(CombatError, match="encounter is finished"):
        enc.perform(Side.ENEMY, Action.ATTACK)


def test_winding_up_flag_is_validated_and_off_by_default():
    assert character().winding_up is False
    with pytest.raises(TypeError):
        character(winding_up="yes")


# --- enemy script --------------------------------------------------------


def test_enemy_script_without_heavy_always_attacks():
    enc = Encounter(character(), character())
    assert [enemy_action(n, enc, heavy=False) for n in range(1, 10)] == [Action.ATTACK] * 9


def test_enemy_script_with_heavy_repeats_attack_wind_up_heavy():
    enc = Encounter(character(), character())
    plan = [enemy_action(n, enc, heavy=True) for n in range(1, 7)]
    assert plan == [
        Action.ATTACK,
        Action.WIND_UP,
        Action.ATTACK,
        Action.ATTACK,
        Action.WIND_UP,
        Action.ATTACK,
    ]


# --- simulation ----------------------------------------------------------

ENEMY_EVENTS = ("Enemy attacks", "Enemy unleashes", "!! Enemy")

WARNING = "!! Enemy is winding up a HEAVY ATTACK. It strikes on its next turn for 5 damage unless you defend."


def play(script, player=(3, 12), enemy=(2, 10)):
    return run(script.read, script.write, maker(*player), maker(*enemy), heavy=True)


def test_warning_appears_on_enemys_second_turn_before_player_responds():
    s = Script("a", "a", "q")

    play(s)

    enemy_lines = [line for line in s.lines if line.startswith(ENEMY_EVENTS)]
    assert enemy_lines[:2] == [
        "Enemy attacks Player for 2 damage. Player HP 10 | Enemy HP 7",
        WARNING,
    ]
    i = s.lines.index(WARNING)
    assert s.lines[i + 1] == "-- Player's turn -- (HEAVY ATTACK INCOMING)"
    # The player was prompted after the warning and before any heavy attack.
    assert s.prompts.count("[a]ttack, [d]efend or [q]uit > ") == 3
    assert not s.lines_with("HEAVY ATTACK on")


def test_sim_defend_blocks_the_heavy_attack():
    s = Script("a", "a", "d", "q")

    play(s)

    assert s.lines_with("HEAVY ATTACK on") == [
        "Enemy unleashes a HEAVY ATTACK on Player, but the attack is blocked! Player HP 10 | Enemy HP 4"
    ]


def test_sim_attacking_lets_the_heavy_attack_land():
    s = Script("a", "a", "a", "q")

    play(s)

    assert s.lines_with("HEAVY ATTACK on") == [
        "Enemy unleashes a HEAVY ATTACK on Player for 5 damage. Player HP 5 | Enemy HP 1"
    ]


def test_sim_returns_to_normal_attacks_after_heavy():
    s = Script("a", "a", "d", "a", "q")

    play(s)

    enemy_hits = [line for line in s.lines if line.startswith(ENEMY_EVENTS)]
    assert enemy_hits[-1] == "Enemy attacks Player for 2 damage. Player HP 8 | Enemy HP 1"
    assert len(s.lines_with("winding up")) == 1


def test_choice_at_warning_decides_this_fight():
    # Player 3/7 vs enemy 2/10: attacking through the heavy attack loses,
    # defending against it wins.
    attack, defend = Script("a", "a", "a", "n"), Script("a", "a", "d", "a", "a", "n")

    assert play(attack, player=(3, 7)) == [LOST]
    assert play(defend, player=(3, 7)) == [WON]


def test_second_encounter_restarts_enemy_script():
    win = ["a", "a", "a", "a"]
    s = Script(*win, "y", *win, "n")

    assert play(s) == [WON, WON]
    assert len(s.lines_with("winding up")) == 2
    second = s.lines[s.lines.index("\n=== Encounter 2 ===") :]
    assert [line for line in second if line.startswith(ENEMY_EVENTS)][1] == WARNING


def test_invalid_input_during_warning_reprompts_without_change():
    s = Script("a", "a", "zzz", "d", "q")

    play(s)

    assert "Unrecognized choice 'zzz'. Options: a, attack, d, defend, q, quit." in s.lines
    assert s.lines_with("HEAVY ATTACK on")[0].endswith("blocked! Player HP 10 | Enemy HP 4")


def test_baseline_sim_has_no_heavy_attacks():
    s = Script("a", "a", "a", "a", "n")

    run(s.read, s.write, maker(3, 12), maker(2, 10))

    assert not s.lines_with("HEAVY")
    assert not s.lines_with("EXPERIMENTAL")


def test_module_launch_with_heavy_flag():
    proc = subprocess.run(
        [sys.executable, "-m", "game.sim", "--heavy"],
        input="a\na\nd\na\na\nn\n",
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    assert WARNING in proc.stdout
    assert "HEAVY ATTACK on Player, but the attack is blocked!" in proc.stdout
    assert "Goodbye. Encounters finished: 1 (won 1, lost 0)." in proc.stdout
