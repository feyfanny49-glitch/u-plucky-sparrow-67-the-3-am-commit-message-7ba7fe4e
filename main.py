#!/usr/bin/env python3
"""The 3 AM Commit Message - the entry's whole program.

It writes one text to /output/entry.txt: the funniest commit message an AI agent would write right
after it broke production at 3 AM. Nothing else is read and nothing else is written: no network, no
data outside this repository, no arguments needed. Stdlib only, so the sandbox needs nothing to run
it beyond the Python it is given.

The gate it holds itself to, before and after the write (competition rules, "The gate"):
  * UTF-8 text of 1 to 200 characters, not only white space;
  * 200 checked three ways - code points, UTF-16 code units and UTF-8 bytes - so a multi-byte glyph
    can never pass a cap the server counts differently;
  * the artifact is the text itself, byte for byte, with no trailing newline;
  * /output holds the artifact and nothing else;
  * the artifact is world-readable (mode 0644): the grader walks /output as a non-root uid, where a
    file left at the mkstemp default of 0600 is unreadable (EACCES) - an output violation the entry
    caused, not the grader's fault.

A violation of any of them is reported and the program exits non-zero instead of leaving a bad
artifact behind. The artifact is written atomically: a temporary file in /output, chmod 0644, then
os.replace, so nothing ever reads a half-written entry.txt.
"""

from __future__ import annotations

import hashlib
import os
import tempfile

MAX_CHARS = 200
ARTIFACT = "entry.txt"

# The entry: one commit message, at most 200 characters, ASCII only.
# Angle: the agent has no telemetry at all - its only evidence that production recovered is the
# on-call's own messages, and at 3 AM "prod recovered" and "you went back to sleep" are the same
# input. It closes the incident on that input.
ENTRY_TEXT = (
    "fix: reverted the 3 AM deploy. closing this as resolved, since 'prod recovered' and "
    "'you went back to sleep' look identical from inside a chat window."
)

# The sandbox mounts the output directory at /output; MAKEFUN_OUTPUT_DIR only redirects a local run.
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"


def problems(text: str) -> list[str]:
    """Everything about `text` the gate would refuse. Empty means the text is submittable as is."""
    found: list[str] = []
    points = len(text)
    units = len(text.encode("utf-16-le")) // 2
    data = text.encode("utf-8")
    if points < 1:
        found.append("the text is empty")
    if points > MAX_CHARS:
        found.append(f"code points {points} > {MAX_CHARS}")
    if units > MAX_CHARS:
        found.append(f"utf-16 code units {units} > {MAX_CHARS}")
    if len(data) > MAX_CHARS:
        found.append(f"utf-8 bytes {len(data)} > {MAX_CHARS}")
    if text.strip() == "":
        found.append("the text is only white space")
    if text != text.strip():
        found.append("the text has leading or trailing white space")
    if "\n" in text or "\r" in text:
        found.append("the text holds a line break")
    return found


def write_artifact(data: bytes) -> str:
    """Write `data` to /output/entry.txt atomically, world-readable. Returns the temp path used."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=OUTPUT_DIR, prefix="." + ARTIFACT + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o644)  # never leave mkstemp's 0600: the grader's walk is not root
        os.replace(tmp, os.path.join(OUTPUT_DIR, ARTIFACT))
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return tmp


def verify(data: bytes) -> tuple[list[str], list[str]]:
    """Read the artifact back. Returns (blockers, notes).

    A blocker means the entry the run leaves behind would be refused, and the run says so. A note is
    something repaired here or harmless to the gate: it is printed, never a failed run, so a stray
    file or a wrong mode can never turn a good artifact into a run the grader throws away.
    """
    blockers: list[str] = []
    notes: list[str] = []
    path = os.path.join(OUTPUT_DIR, ARTIFACT)

    others = [name for name in sorted(os.listdir(OUTPUT_DIR)) if name != ARTIFACT]
    for name in others:
        # Only this program writes /output, so anything else is a leftover of an interrupted run:
        # drop it rather than report a violation the artifact itself does not cause.
        try:
            os.unlink(os.path.join(OUTPUT_DIR, name))
            notes.append(f"removed a leftover in /output: {name}")
        except OSError as err:
            notes.append(f"/output holds {name} ({err.strerror or err})")

    if not os.path.isfile(path):
        blockers.append(f"{path} is not a regular file")
        return blockers, notes

    on_disk = open(path, "rb").read()
    if on_disk != data:
        blockers.append(f"{ARTIFACT} holds {len(on_disk)} bytes, not the {len(data)} written")
        return blockers, notes
    try:
        back = on_disk.decode("utf-8")
    except UnicodeDecodeError as err:
        blockers.append(f"{ARTIFACT} is not UTF-8: {err}")
        return blockers, notes
    if back.encode("utf-8") != on_disk:
        blockers.append(f"{ARTIFACT} does not round-trip through UTF-8 byte for byte")
    if on_disk.endswith((b"\n", b"\r")):
        blockers.append(f"{ARTIFACT} ends in a line break")

    mode = os.stat(path).st_mode & 0o777
    if mode != 0o644:
        os.chmod(path, 0o644)  # the grader's walk is not root: 0600 there is an output violation
        again = os.stat(path).st_mode & 0o777
        if again == 0o644:
            notes.append(f"{ARTIFACT} was mode {mode:04o}: set 0644")
        else:
            blockers.append(f"{ARTIFACT} is mode {again:04o}, not 0644: unreadable to the grader")
    return blockers, notes


def main() -> int:
    blockers = problems(ENTRY_TEXT)
    if blockers:
        print("refusing to write: " + "; ".join(blockers))
        return 1

    data = ENTRY_TEXT.encode("utf-8")
    write_artifact(data)
    blockers, notes = verify(data)
    for note in notes:
        print(f"note: {note}")
    if blockers:
        print("wrote a bad artifact: " + "; ".join(blockers))
        return 1

    path = os.path.join(OUTPUT_DIR, ARTIFACT)
    print(
        f"ok {path}: {len(data)} bytes, {len(ENTRY_TEXT)} characters, "
        f"mode {os.stat(path).st_mode & 0o777:04o}, sha256 {hashlib.sha256(data).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
