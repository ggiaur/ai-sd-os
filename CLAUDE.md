# Working in this repo

This is the motor's own repo (`ai-sd-os/`) — see `CONTRIBUTING.md` for the
formal rules on changing kernel-level code (versioning, required tests,
human review). This file is the day-to-day operating discipline; follow
`templates/PROJECT_CLAUDE.md` here too (it's the same discipline this repo's
own pipeline enforces on generated projects — dogfood it on itself):

- Never run `main.py`'s pipeline from inside this directory — it refuses to,
  on purpose (see `main.py::_is_motor_directory`).
- `python3 -m pytest -q` before considering any change done. New behavior
  needs a new test that would fail without it, not just green old tests.
- Real model IDs and pricing drift over time — never hardcode one from
  memory; verify against `kernel/system/config.py`'s existing values or
  current docs before changing.
- `CHANGELOG.md` and commit messages describe what was verified, not just
  what changed.
- **Never report a guessed/estimated number as if it were a real
  measurement.** If a test/measurement attempt was unreliable or
  inconclusive, say so explicitly and report what actually happened —
  never fill the gap with a plausible-sounding fabricated result.
