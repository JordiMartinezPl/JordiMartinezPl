from __future__ import annotations

import datetime as _dt
import os
import pathlib
import tempfile

import wordle


def check_scoring() -> None:
    assert wordle.score_guess("MOUNT", "MOUNT") == ["hit"] * 5
    assert wordle.score_guess("BREAK", "MOUNT") == ["miss"] * 5
    r = wordle.score_guess("SPLIT", "SHIFT")
    assert r[0] == "hit"
    assert r[4] == "hit"
    assert r[3] == "near"
    r2 = wordle.score_guess("EERIE", "THERE")
    assert r2[4] == "hit", r2
    print("scoring: OK")


def play(answer: str, guesses: list[str]) -> None:
    tmp = tempfile.mkdtemp()
    os.environ["GITHUB_REPOSITORY"] = "JordiMartinezPl/JordiMartinezPl"
    os.environ["GAME_TODAY"] = "2026-08-04"

    import importlib
    import engine
    importlib.reload(engine)
    engine.SAVES_DIR = pathlib.Path(tmp) / "saves"
    engine.LEADERBOARD = pathlib.Path(tmp) / "leaderboard.json"
    engine.COMMENT_OUT = pathlib.Path(tmp) / "_comment.md"
    engine.README = pathlib.Path(tmp) / "README.md"

    day = _dt.date(2026, 8, 4)
    orig = wordle.word_of_the_day
    wordle.word_of_the_day = lambda d: answer
    try:
        for g in guesses:
            comment = engine.run("demo-player", f"CMDLE {g}", day=day)
            print("=" * 56)
            print(comment)
    finally:
        wordle.word_of_the_day = orig


if __name__ == "__main__":
    check_scoring()
    print("\n### winning game (answer = MOUNT) ###")
    play("MOUNT", ["PASTE", "SHRED", "CLOWN", "MOUNT"])
    print("\n### losing + invalid guess (answer = CHMOD) ###")
    play("CHMOD", ["XXXX", "PASTE", "SHRED", "BREAK", "SPLIT", "FALSE", "WATCH"])
