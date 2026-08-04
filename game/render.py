from __future__ import annotations

import urllib.parse

from wordle import (
    HIT,
    MAX_GUESSES,
    MISS,
    NEAR,
    WORD_LEN,
    keyboard_state,
    score_guess,
)

SQUARE = {HIT: "🟩", NEAR: "🟨", MISS: "⬛"}
EMPTY_SQUARE = "⬜"
EMPTY_ROW_LETTERS = "·" * WORD_LEN


def board(guesses: list[str], answer: str) -> str:
    lines = []
    for g in guesses:
        squares = "".join(SQUARE[m] for m in score_guess(g, answer))
        lines.append(f"  {'  '.join(g)}   {squares}")
    for _ in range(MAX_GUESSES - len(guesses)):
        squares = EMPTY_SQUARE * WORD_LEN
        lines.append(f"  {'  '.join(EMPTY_ROW_LETTERS)}   {squares}")
    body = "\n".join(lines)
    return f"```\n{body}\n```"


def keyboard(guesses: list[str], answer: str) -> str:
    state = keyboard_state(guesses, answer)
    if not state:
        return ""
    correct = sorted(c for c, m in state.items() if m == HIT)
    present = sorted(c for c, m in state.items() if m == NEAR)
    absent = sorted(c for c, m in state.items() if m == MISS)
    parts = []
    if correct:
        parts.append(f"🟩 `{' '.join(correct)}`")
    if present:
        parts.append(f"🟨 `{' '.join(present)}`")
    if absent:
        parts.append(f"⬛ ~~`{' '.join(absent)}`~~")
    return "  ·  ".join(parts)


def guess_link(repo: str, label: str = "🔤 Type my guess") -> str:
    title = "CMDLE XXXXX"
    body = (
        "👆 Replace the **XXXXX** in the title above with your 5-letter guess "
        "and hit **Submit new issue**.\n\n"
        "You don't need to write anything down here."
    )
    q = urllib.parse.urlencode({"title": title, "body": body, "labels": "cmdle"})
    return f"[{label}](https://github.com/{repo}/issues/new?{q})"


def issue_comment(state: dict, repo: str, *, invalid: str | None = None) -> str:
    guesses = state["guesses"]
    answer = state["answer"]
    status = state["status"]
    left = MAX_GUESSES - len(guesses)

    out = ["### 🟩 Guess the terminal command", ""]
    if invalid:
        out += [f"> ⚠️ {invalid}", ""]
    out.append(board(guesses, answer))
    kb = keyboard(guesses, answer)
    if kb:
        out += ["", kb]
    out.append("")

    if status == "won":
        n = len(guesses)
        out += [
            f"🎉 **Solved in {n}/{MAX_GUESSES}!** The command was `{answer.lower()}`.",
            "",
            "Come back tomorrow for the next one — and share your result 👀",
        ]
    elif status == "lost":
        out += [
            f"💀 **Out of tries.** The command was `{answer.lower()}`.",
            "",
            "A fresh command drops every day. Good luck!",
        ]
    else:
        hint = "" if guesses else " _(it's a real 5-letter shell command)_"
        out += [
            f"You have **{left}** guess(es) left.{hint}  {guess_link(repo)}",
            "",
            "<sub>After you submit, this issue closes itself — that's expected. "
            "Your result shows up here in a few seconds.</sub>",
        ]
    return "\n".join(out)


def readme_demo_board() -> str:
    rows = [
        ("PASTE", [MISS, NEAR, MISS, MISS, HIT]),
        ("SHRED", [MISS, MISS, MISS, MISS, MISS]),
        ("MOUNT", [HIT, HIT, HIT, HIT, HIT]),
    ]
    lines = []
    for word, marks in rows:
        squares = "".join(SQUARE[m] for m in marks)
        lines.append(f"  {'  '.join(word)}   {squares}")
    for _ in range(MAX_GUESSES - len(rows)):
        lines.append(f"  {'  '.join(EMPTY_ROW_LETTERS)}   {EMPTY_SQUARE * WORD_LEN}")
    body = "\n".join(lines)
    return f"```\n{body}\n```"


def readme_leaderboard(leaderboard: dict) -> str:
    today = leaderboard.get("today", [])
    alltime = leaderboard.get("alltime", {})

    out = []
    out.append("**🏆 Today's solvers**")
    out.append("")
    if today:
        ranked = sorted(today, key=lambda r: r["guesses"])
        out.append("| # | player | guesses |")
        out.append("|---|--------|:-------:|")
        for i, r in enumerate(ranked[:10], 1):
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}")
            out.append(f"| {medal} | [@{r['user']}](https://github.com/{r['user']}) | {r['guesses']}/6 |")
    else:
        out.append("_Nobody has cracked today's command yet. Be the first?_")

    streaks = sorted(
        ((u, s) for u, s in alltime.items() if s.get("streak", 0) > 0),
        key=lambda kv: kv[1]["streak"],
        reverse=True,
    )
    if streaks:
        out += ["", "**🔥 Longest streaks**", ""]
        out.append("| player | streak | wins |")
        out.append("|--------|:------:|:----:|")
        for u, s in streaks[:5]:
            out.append(f"| [@{u}](https://github.com/{u}) | {s['streak']} 🔥 | {s.get('won', 0)} |")

    return "\n".join(out)
