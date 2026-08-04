from __future__ import annotations

import datetime as _dt
import json
import os
import pathlib
import re

import render
import wordle

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SAVES_DIR = HERE / "saves"
LEADERBOARD = HERE / "leaderboard.json"
COMMENT_OUT = HERE / "_comment.md"
README = ROOT / "README.md"

LB_START = "<!-- LEADERBOARD:START -->"
LB_END = "<!-- LEADERBOARD:END -->"

TITLE_RE = re.compile(r"^\s*CMDLE\b\s*(.*)$", re.IGNORECASE)


def today(default: _dt.date | None = None) -> _dt.date:
    override = os.environ.get("GAME_TODAY")
    if override:
        return _dt.date.fromisoformat(override)
    return default or _dt.datetime.now(_dt.timezone.utc).date()


def repo() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "JordiMartinezPl/JordiMartinezPl")


def extract_guess(title: str) -> str | None:
    m = TITLE_RE.match(title or "")
    if not m:
        return None
    return wordle.normalize(m.group(1))


def _read_json(path: pathlib.Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _write_json(path: pathlib.Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_state(user: str, day: _dt.date) -> dict:
    path = SAVES_DIR / f"{user.lower()}.json"
    state = _read_json(path, None)
    iso = day.isoformat()
    if not state or state.get("date") != iso:
        state = {
            "user": user,
            "date": iso,
            "answer": wordle.word_of_the_day(day),
            "guesses": [],
            "status": "playing",
        }
    return state


def save_state(state: dict) -> None:
    path = SAVES_DIR / f"{state['user'].lower()}.json"
    _write_json(path, state)


def load_leaderboard(day: _dt.date) -> dict:
    lb = _read_json(LEADERBOARD, {"date": day.isoformat(), "today": [], "alltime": {}})
    if lb.get("date") != day.isoformat():
        lb["date"] = day.isoformat()
        lb["today"] = []
    lb.setdefault("alltime", {})
    return lb


def record_result(lb: dict, state: dict, day: _dt.date) -> None:
    user = state["user"]
    won = state["status"] == "won"
    guesses = len(state["guesses"])

    if won and not any(r["user"] == user for r in lb["today"]):
        lb["today"].append({"user": user, "guesses": guesses})

    a = lb["alltime"].setdefault(
        user, {"played": 0, "won": 0, "streak": 0, "best": 0, "last": None}
    )
    a["played"] += 1
    yesterday = (day - _dt.timedelta(days=1)).isoformat()
    if won:
        a["won"] += 1
        a["streak"] = a["streak"] + 1 if a.get("last") == yesterday else 1
        a["best"] = max(a.get("best", 0), a["streak"])
    else:
        a["streak"] = 0
    a["last"] = day.isoformat()


def play_turn(state: dict, guess: str | None) -> tuple[dict, str | None]:
    if state["status"] != "playing":
        return state, None
    if guess is None or not wordle.is_valid_guess(guess):
        return state, "That wasn't a 5-letter word. Try again with exactly 5 letters (A–Z)."
    if guess in state["guesses"]:
        return state, f"You already guessed `{guess.lower()}`."

    state["guesses"].append(guess)
    marks = wordle.score_guess(guess, state["answer"])
    if wordle.is_solved(marks):
        state["status"] = "won"
    elif len(state["guesses"]) >= wordle.MAX_GUESSES:
        state["status"] = "lost"
    return state, None


def update_readme(lb: dict) -> None:
    if not README.exists():
        return
    text = README.read_text(encoding="utf-8")
    if LB_START not in text or LB_END not in text:
        return
    block = f"{LB_START}\n{render.readme_leaderboard(lb)}\n{LB_END}"
    new = re.sub(
        re.escape(LB_START) + r".*?" + re.escape(LB_END),
        lambda _m: block,
        text,
        flags=re.DOTALL,
    )
    if new != text:
        README.write_text(new, encoding="utf-8")


def run(user: str, title: str, day: _dt.date | None = None) -> str:
    day = today(day)
    state = load_state(user, day)
    already_done = state["status"] != "playing"

    guess = extract_guess(title)
    state, invalid = play_turn(state, guess)
    save_state(state)

    if state["status"] != "playing" and not already_done:
        lb = load_leaderboard(day)
        record_result(lb, state, day)
        _write_json(LEADERBOARD, lb)
        update_readme(lb)

    if already_done:
        invalid = "You already played today — come back tomorrow for a new command."

    comment = render.issue_comment(state, repo(), invalid=invalid)
    COMMENT_OUT.write_text(comment + "\n", encoding="utf-8")
    return comment


def main() -> None:
    user = os.environ.get("ISSUE_AUTHOR", "").strip()
    title = os.environ.get("ISSUE_TITLE", "").strip()
    if not user:
        raise SystemExit("ISSUE_AUTHOR is required")
    run(user, title)


if __name__ == "__main__":
    main()
