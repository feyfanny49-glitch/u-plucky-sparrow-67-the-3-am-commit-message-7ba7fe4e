#!/usr/bin/env python3
"""Local reproduction of the gate for this competition, and of the grader's output walk.

Usage:
    python3 tools/validate_entry.py [output_dir]

Checks, in the gate's own order:
  1. /output holds entry.txt and nothing else (an extra file is an output violation).
  2. entry.txt is UTF-8 text (strict decode of the raw bytes).
  3. 1 <= len(text) <= 200 characters, counted three ways (code points, UTF-8 bytes, UTF-16 units)
     so a multi-byte glyph can never sneak past the cap.
  4. the text is not only white space.
  5. the file is world-readable (mode 0644, i.e. no 0600 left from mkstemp); the grader walks
     /output as a non-root uid and EACCES there is an output violation.
  6. there is no trailing newline (the artifact is the text itself, byte for byte).

Exit 0 when every check passes, 1 otherwise. Prints one line per check.
"""

from __future__ import annotations

import os
import sys

MAX_CHARS = 200
ARTIFACT = "entry.txt"


def main(argv: list[str]) -> int:
    out_dir = argv[1] if len(argv) > 1 else "/output"
    path = os.path.join(out_dir, ARTIFACT)
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str) -> None:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
        if not ok:
            failures.append(name)

    if not os.path.isdir(out_dir):
        print(f"FAIL  output dir: {out_dir} is not a directory")
        return 1

    listing = sorted(os.listdir(out_dir))
    check("output holds the artifact alone", listing == [ARTIFACT], f"{listing}")

    if not os.path.isfile(path):
        print(f"FAIL  artifact: {path} is missing")
        return 1

    raw = open(path, "rb").read()
    st = os.stat(path)

    try:
        text = raw.decode("utf-8")
        check("utf-8", True, f"{len(raw)} bytes decode as UTF-8")
    except UnicodeDecodeError as err:
        check("utf-8", False, str(err))
        return 1

    code_points = len(text)
    utf16_units = len(text.encode("utf-16-le")) // 2
    check(
        f"1..{MAX_CHARS} characters",
        code_points >= 1 and code_points <= MAX_CHARS and utf16_units <= MAX_CHARS and len(raw) <= MAX_CHARS,
        f"code points {code_points}, utf-16 units {utf16_units}, utf-8 bytes {len(raw)}",
    )
    check("not only white space", text.strip() != "", f"stripped length {len(text.strip())}")
    check("no trailing newline", not raw.endswith((b"\n", b"\r")), f"last byte {raw[-1:]!r}")

    mode = st.st_mode & 0o777
    check("world-readable mode 0644", mode == 0o644, f"mode {mode:04o}")

    if raw != text.encode("utf-8"):
        failures.append("byte-for-byte")

    print()
    print(f"--- text ({len(raw)} bytes) ---")
    print(text)
    print("--- end ---")
    if failures:
        print(f"RESULT: FAIL ({', '.join(failures)})")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
