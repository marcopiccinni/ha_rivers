---
description: Validate the ha_rivers integration locally (syntax + JSON + lint) before committing
agent: build
---

Run the local validation for the `ha_rivers` integration and report a concise
pass/fail summary:

1. `python -m compileall custom_components/ha_rivers`
2. Validate every JSON file under `custom_components/ha_rivers` parses.
3. `ruff check custom_components/ha_rivers` if `ruff` is available (skip
   gracefully otherwise).
4. Confirm `manifest.json` version matches the latest `CHANGELOG.md` entry.

Do not push, tag or create releases. Just report results and any fixes needed.
