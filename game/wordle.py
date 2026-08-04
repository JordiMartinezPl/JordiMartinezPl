from __future__ import annotations

import datetime as _dt
import unicodedata

from words import ANSWERS

WORD_LEN = 5
MAX_GUESSES = 6

HIT = "hit"
NEAR = "near"
MISS = "miss"

EPOCH = _dt.date(2026, 1, 1)


def normalize(raw: str) -> str:
    raw = raw.strip().upper()
    decomposed = unicodedata.normalize("NFKD", raw)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    stripped = stripped.replace("Ñ", "N")
    return "".join(c for c in stripped if "A" <= c <= "Z")


def is_valid_guess(guess: str) -> bool:
    return len(guess) == WORD_LEN and guess.isalpha()


def daily_index(day: _dt.date) -> int:
    return (day.toordinal() - EPOCH.toordinal()) % len(ANSWERS)


def word_of_the_day(day: _dt.date) -> str:
    return ANSWERS[daily_index(day)]


def score_guess(guess: str, answer: str) -> list[str]:
    guess = guess.upper()
    answer = answer.upper()
    marks = [MISS] * WORD_LEN

    remaining: dict[str, int] = {}
    for i, ch in enumerate(answer):
        if guess[i] == ch:
            marks[i] = HIT
        else:
            remaining[ch] = remaining.get(ch, 0) + 1

    for i, ch in enumerate(guess):
        if marks[i] == HIT:
            continue
        if remaining.get(ch, 0) > 0:
            marks[i] = NEAR
            remaining[ch] -= 1

    return marks


def is_solved(marks: list[str]) -> bool:
    return all(m == HIT for m in marks)


def keyboard_state(guesses: list[str], answer: str) -> dict[str, str]:
    rank = {MISS: 0, NEAR: 1, HIT: 2}
    state: dict[str, str] = {}
    for g in guesses:
        for ch, mk in zip(g, score_guess(g, answer)):
            if ch not in state or rank[mk] > rank[state[ch]]:
                state[ch] = mk
    return state
