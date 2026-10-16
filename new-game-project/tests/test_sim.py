import subprocess
import sys

import pytest

from game.combat import Character, Traits
from game.sim import LOST, WON, run


class Script:
    """Feeds scripted answers to the simulation and records everything shown."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.prompts = []
        self.lines = []

    def read(self, prompt):
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def write(self, text):
        self.lines.append(text)

    @property
    def text(self):
        return "\n".join(self.lines)

    def lines_with(self, fragment):
        return [line for line in self.lines if fragment in line]


def maker(puissant, health):
    return lambda: Character(
        Traits(puissant=puissant, alacrity=0, measure=0, aptitude=0, acumen=0, glamour=0),
        health=health,
    )


def play(script, player=(3, 12), enemy=(2, 10)):
    return run(script.read, script.write, maker(*player), maker(*enemy))


# Default prototype stats: player Puissant 3 / HP 12, enemy Puissant 2 / HP 10.
# Player hits for 3 (10 -> 7 -> 4 -> 1 -> 0); enemy hits for 2 three times.
PLAYER_WIN = ["a", "a", "a", "a"]


def test_initial_state_shows_both_characters_with_all_six_traits():
    s = Script("q")

    run(s.read, s.write)

    assert "=== Encounter 1 ===" in s.text
    assert "Player HP  12 | Puissant 3  Alacrity 2  Measure 2  Aptitude 1  Acumen 1  Glamour 1" in s.lines
    assert "Enemy  HP  10 | Puissant 2  Alacrity 1  Measure 1  Aptitude 0  Acumen 0  Glamour 0" in s.lines
    assert "-- Player's turn --" in s.lines


def test_player_attack_is_followed_by_automatic_enemy_attack():
    s = Script("a", "q")

    play(s)

    assert s.lines_with("attacks") == [
        "Player attacks Enemy for 3 damage. Player HP 12 | Enemy HP 7",
        "Enemy attacks Player for 2 damage. Player HP 10 | Enemy HP 7",
    ]
    # The player was prompted only on their own turns.
    assert s.prompts == ["[a]ttack, [d]efend or [q]uit > "] * 2


def test_victory_is_reported_and_no_extra_attacks_happen():
    s = Script(*PLAYER_WIN, "n")

    outcomes = play(s)

    assert outcomes == [WON]
    assert "Victory! The enemy is defeated." in s.lines
    attacks = s.lines_with("attacks")
    assert len(attacks) == 7  # 4 player + 3 enemy; the lethal hit ends it
    assert attacks[-1] == "Player attacks Enemy for 1 damage. Player HP 6 | Enemy HP 0"
    after_victory = s.lines[s.lines.index("Victory! The enemy is defeated.") :]
    assert not any("attacks" in line or "turn --" in line for line in after_victory)


def test_defeat_is_reported_when_enemy_wins():
    s = Script("a", "a", "n")

    outcomes = play(s, player=(1, 4), enemy=(2, 10))

    assert outcomes == [LOST]
    assert s.lines_with("attacks")[-1] == "Enemy attacks Player for 2 damage. Player HP 0 | Enemy HP 8"
    assert "Defeat. You have fallen." in s.lines
    assert "Victory" not in s.text


def test_overkill_reports_damage_actually_applied():
    s = Script("a", "n")

    play(s, player=(9, 5), enemy=(1, 3))

    assert s.lines_with("attacks") == ["Player attacks Enemy for 3 damage. Player HP 5 | Enemy HP 0"]


def test_second_encounter_starts_fresh_after_first_finishes():
    s = Script(*PLAYER_WIN, "y", *PLAYER_WIN, "n")

    outcomes = play(s)

    assert outcomes == [WON, WON]
    assert "=== Encounter 2 ===" in s.text
    second = s.lines[s.lines.index("\n=== Encounter 2 ===") :]
    assert "Player HP  12 | Puissant 3  Alacrity 0  Measure 0  Aptitude 0  Acumen 0  Glamour 0" in second
    assert s.lines[-1] == "Goodbye. Encounters finished: 2 (won 2, lost 0)."


def test_identical_input_produces_identical_output():
    first, second = Script(*PLAYER_WIN, "n"), Script(*PLAYER_WIN, "n")

    play(first)
    play(second)

    assert first.lines == second.lines


@pytest.mark.parametrize("bad", ["x", "", "  ", "attack!", "2"])
def test_invalid_turn_input_reprompts_without_changing_state(bad):
    s = Script(bad, "a", "q")

    play(s)

    assert any("Unrecognized choice" in line for line in s.lines)
    # Exactly one exchange happened, same as with no invalid input.
    assert len(s.lines_with("attacks")) == 2
    assert s.lines_with("attacks")[0] == "Player attacks Enemy for 3 damage. Player HP 12 | Enemy HP 7"


def test_input_is_case_and_whitespace_insensitive():
    s = Script("  A ", "Attack", "Q")

    play(s)

    assert len(s.lines_with("attacks")) == 4


def test_invalid_play_again_input_reprompts():
    s = Script(*PLAYER_WIN, "maybe", "n")

    outcomes = play(s)

    assert outcomes == [WON]
    assert "Unrecognized choice 'maybe'. Options: n, no, q, quit, y, yes." in s.lines
    assert s.prompts.count("Fight again? [y]es / [n]o > ") == 2


def test_quit_mid_encounter_ends_cleanly_without_an_outcome():
    s = Script("a", "q")

    outcomes = play(s)

    assert outcomes == []
    assert "Victory" not in s.text and "Defeat" not in s.text
    assert s.lines[-1] == "Goodbye. Encounters finished: 0 (won 0, lost 0)."


def test_end_of_input_quits_cleanly():
    s = Script("a")  # input runs out on the next prompt

    assert play(s) == []
    assert s.lines[-1].startswith("Goodbye.")


# --- defend (PROVISIONAL) ------------------------------------------------


def test_defend_blocks_the_enemy_attack_and_is_reported():
    s = Script("d", "q")

    play(s)

    assert s.lines_with("defends") == ["Player defends and will block the next attack."]
    blocked = s.lines_with("blocked")
    assert blocked == ["Enemy attacks Player, but the attack is blocked! Player HP 12 | Enemy HP 10"]
    assert "damage" not in blocked[0]


def test_block_is_used_up_so_the_following_enemy_attack_hits():
    s = Script("d", "a", "q")

    play(s)

    assert s.lines_with("Enemy attacks") == [
        "Enemy attacks Player, but the attack is blocked! Player HP 12 | Enemy HP 10",
        "Enemy attacks Player for 2 damage. Player HP 10 | Enemy HP 7",
    ]


def test_defend_accepts_word_and_mixed_case():
    s = Script(" Defend ", "D", "q")

    play(s)

    assert len(s.lines_with("defends")) == 2
    assert len(s.lines_with("blocked")) == 2


def test_defend_prevents_otherwise_lethal_hit_in_sim():
    # Enemy Puissant 9 would kill a 4 HP player; defending saves them once.
    s = Script("d", "a", "n")

    outcomes = play(s, player=(1, 4), enemy=(9, 10))

    assert s.lines_with("Enemy attacks") == [
        "Enemy attacks Player, but the attack is blocked! Player HP 4 | Enemy HP 10",
        "Enemy attacks Player for 4 damage. Player HP 0 | Enemy HP 9",
    ]
    assert outcomes == [LOST]


def test_defend_delays_but_does_not_change_outcome_against_always_attacking_enemy():
    # Documents current PROVISIONAL behavior: a defend turn cancels one full
    # round (no player hit, enemy hit blocked), so the result is unchanged.
    attack_only, with_defend = Script("a", "a", "n"), Script("d", "a", "a", "n")

    assert play(attack_only, player=(1, 4), enemy=(2, 10)) == [LOST]
    assert play(with_defend, player=(1, 4), enemy=(2, 10)) == [LOST]
    assert len(with_defend.lines_with("attacks")) == len(attack_only.lines_with("attacks")) + 1


def test_module_runs_without_interactive_terminal():
    # Launch exactly as documented, with piped (non-tty) stdin.
    proc = subprocess.run(
        [sys.executable, "-m", "game.sim"],
        input="a\na\na\na\nn\n",
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    assert "Victory! The enemy is defeated." in proc.stdout
    assert "Goodbye. Encounters finished: 1 (won 1, lost 0)." in proc.stdout
