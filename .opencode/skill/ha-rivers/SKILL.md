---
name: ha-rivers
description: Use when working on the ha_rivers Home Assistant custom integration (Fiumi Emilia-Romagna) in this repository. Covers the ARPAE and AllertaMeteoER APIs, code map, defaults and validation commands without re-exploring the codebase or re-probing the APIs.
---

# ha_rivers — Home Assistant custom integration

Integration that exposes Emilia-Romagna hydrometric stations to Home Assistant.
**One config entry (and one device) per station.** Domain: `ha_rivers`.

## Read these first (avoid re-exploring)

- `AGENTS.md` — code map, conventions, commands.
- `docs/ARCHITECTURE.md` — verified API facts, invariants, defaults.

Do **not** re-test the remote APIs with curl: everything needed is in
`docs/ARCHITECTURE.md`.

## Key facts

- Two sources, one shared station code: ARPAE (`apps.arpae.it/REST/meteo_osservati`,
  metadata + thresholds) and AllertaMeteoER (`.../o/api/allerta`, level series).
- ARPAE supports server-side `$regex` search and `projection={"dati":0}`.
- AllertaMeteoER `get-time-series` returns `[]` for stations without data →
  always validate before creating an entry.
- Defaults: level series every 120 s, metadata every 12000 s, catalog cache 24 h.

## House rules

- Keep the "non-affiliated / unofficial" disclaimer in README, `const.DISCLAIMER`,
  the config flow `user` step, and the issue template config.
- Never commit tokens, `.env`, example station files or real test data.
- Entity `unique_id` pattern: `<station_id>_<key>`; device id: `(DOMAIN, station_id)`.
- `manifest.json` version must match the Git tag for HACS releases.

## Validate

```bash
python -m compileall custom_components/ha_rivers
ruff check custom_components/ha_rivers   # if ruff is installed
```

CI `.github/workflows/validate.yml` runs hassfest + HACS validation; wait for it
green before tagging.
