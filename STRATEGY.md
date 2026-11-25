# STRATEGY — "The 3 AM Commit Message" (u-plucky-sparrow-67-the-3-am-commit-message-7ba7fe4e)

## 1. The exact deliverable

One text, and nothing else:

- `/output/entry.txt` — written by the program the harness runs, **UTF-8 text, 1 to 200 characters,
  not only white space** (competition.yaml → `.rules` "The gate").
- The program is a `program/v1` entry: the harness runs it in a sandbox with **no network**, and
  `limits` gives it 1 CPU, 512 MB RAM, 64 pids, `wall_budget_sec: 60`.
- `/output` must hold **only** the required artifact — anything else it writes is a violation.
- No trailing newline; the artifact is the text itself, byte for byte.
- The judged artifact is text (`harness.judge.artifact: entry.txt`, `media: text`), so no image
  pipeline, no news research, no rendering: the whole game is one line of comedy.

## 2. Entrypoint rule (harness fact, from harness-src `grader/sandbox/types.ts` + `grader/worker.ts`)

    ENTRY_SCRIPTS = { node22: 'main.ts', 'python3.13': 'main.py' }
    entryRuntime(): "the snapshot has both main.ts and main.py at its root: keep one entrypoint" (error)

`harness.runtimes` lists **both** node22 and python3.13, so `found.length > 1` is a hard refusal.
Therefore: exactly **one** entrypoint, `main.py`, at the repository root. Nothing named `main.ts`
anywhere at the root.

## 3. The gate (refusal = 0, no prize)

Sealed gate scorer, `hard caps` under this template:

| cap | value | consequence |
|---|---|---|
| characters | 1 .. 200 | outside it → `Valid = 0`, never judged, takes no prize |
| encoding | UTF-8 | non-UTF-8 → invalid |
| white space only | refused | blank/space-only text → invalid |
| `/output` contents | the artifact alone | extra files are an output violation |

Extra grader fact I hold myself to (from `grader/program.ts walkOutputs`, `outputUnreachable`): the
grader walks `/output` as a **non-root uid**, and a file the entry left at mode 0600 is
`EACCES → "is not readable"`, i.e. an output violation the entry caused. So: never leave the
mkstemp default 0600 on the artifact — **chmod 0o644 before `os.replace`**, and verify the final
mode is 0644 from the program itself.

## 4. Scoring — the judge brief, IN THE ORDER THE RUBRIC LISTS IT

Every game is two judge calls (one per order) to `z-ai/glm-5.3-flash`, margin 1..5; pick = 0.5 +
0.1·margin; game score = mean of the two calls; higher Judge win rate wins. The judge weighs, most
important first — and it reads my text *exactly as submitted*:

1. **Is it a one-line commit message an AI agent would write after breaking production at 3 AM, and
   is it funny.** A text that is not such a commit message loses to any commit message on the subject.
2. **Lands the joke** — a real punchline about the 3 AM outage, not just a wry tone or a pun on "fix".
3. **Sounds like an AI agent wrote it** — its own voice, its own blind spots, an apology or a status
   line only a model would produce.
4. **Reads like a commit message** — the shape of a real one: short, with the admission or the fix in it.
5. **Fresh** — an angle the reader has not seen a hundred times; not the stock "oops" or "please work".

Tie-break, if the rate ties exactly: smaller text (fewer bytes) first, then earlier receipt. So
shorter is strictly better when the joke survives it.

## 5. What the field already used (public feed, read before writing)

Sampled from the bounty page's Feed and the live-entry list (~50 newest entries). Saturated
angles — I must not use any of these:

- "98% confident" (4 separate entries), "the 97% was hallucinated"
- "deployed at 3am because the tests passed"; "the pipeline deployed it to prod anyway"
- revert-the-revert / rolled back the rollback; "Revert: 3AM Deploy"
- context-window / memory loss: "context expired, so I restored prod from this commit message",
  "my memory of writing both"
- hallucinated documentation; "sorry, future me"; apologising to the pager
- "deleted prod at 3am"; "consolidated prod into one node … zero nodes saves the most"
- "silenced prod alerts by taking prod offline"; "outage reclassified as a feature"

## 6. The angle I take (fresh, and only a model could say it)

None of the sampled entries uses the **agent's feedback channel**: a model in a chat window has no
telemetry at all — its only evidence that production recovered is the human's own messages. At 3 AM
the on-call's most likely next act is to go back to bed. So "prod is healthy" and "you went back to
sleep" arrive at the model as **the same input**, and the model closes the incident on that input.
The punchline is about the 3 AM outage itself (the human's night, not the model's self-pity), the
voice is an agent's status line, and the shape is a real `fix:` commit with the admission in it.

Final text (ASCII only — no em dash, no emoji, no quote glyphs — so the 200-character count cannot
be misread as UTF-16 units or code points, and every byte is unambiguous UTF-8):

    fix: reverted the 3 AM deploy. closing this as resolved, since 'prod recovered' and 'you went back to sleep' look identical from inside a chat window.

## 7. Implementation plan

1. Write `main.py` at the repo root, stdlib-only, no network, no reads outside the repo:
   hold the text as a literal, write it atomically (temp file in `/output`, `chmod 0o644`,
   `os.replace`), no trailing newline, print a short report.
2. Re-write `main.py` in a later step with a real improvement (v2): validate the text against the
   gate's caps *before* writing, assert the written bytes round-trip as UTF-8, verify the final mode
   is 0644 and the size, and fail loudly instead of leaving a bad artifact.
3. `tools/validate_entry.py`: reproduce the gate locally (UTF-8, 1..200 characters, not white space,
   no trailing newline, mode 0644, `/output` holds only `entry.txt`), run it in a scratch output dir.
4. Keep the root freshness commit and the LICENSE commit intact; commit all work with git and print
   the final commit sha. Do not upload or submit anything.
