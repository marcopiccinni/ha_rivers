# AGENTS.md

Istruzioni per assistenti/agenti che lavorano su questo repository. Obiettivo:
minimizzare i token evitando di ri-esplorare il codice o ri-testare le API.

## Panoramica

Integrazione custom Home Assistant (HACS) che espone lo stato idrometrico delle
stazioni dell'Emilia-Romagna. **Una config entry per stazione.**

- Dominio: `ha_rivers`
- Piattaforme: `sensor`, `binary_sensor`
- Dati: ARPAE (metadati) + AllertaMeteoER (serie livello)

## Mappa del codice

| File | Responsabilità |
| --- | --- |
| `custom_components/ha_rivers/const.py` | URL, codici, default, disclaimer |
| `custom_components/ha_rivers/catalog.py` | fetch/cache/ricerca stazioni (entrambe le organizzazioni) |
| `custom_components/ha_rivers/coordinator.py` | polling serie (scan interval) + metadati (metadata interval), calcolo `alert`/`trend`, `RiverData` |
| `custom_components/ha_rivers/config_flow.py` | ricerca → selezione → validazione serie → entry; OptionsFlow |
| `custom_components/ha_rivers/sensor.py` | entità principali ed extra |
| `custom_components/ha_rivers/binary_sensor.py` | stato "stazione attiva" |
| `custom_components/ha_rivers/diagnostics.py` | diagnostica entry |

Dettagli su API, invarianti e decisioni di design: **`docs/ARCHITECTURE.md`**.

## Convenzioni

- Python 3.13+, stile Home Assistant: `async`/`await`, `aiohttp` via
  `async_get_clientsession(hass)`, `DataUpdateCoordinator`, `ConfigEntry.runtime_data`.
- Un `entity_description` per sensore, `_attr_has_entity_name = True`,
  `unique_id = "<station_id>_<key>"`.
- Niente nuove dipendenze in `manifest.json` se non strettamente necessario.
- Mantenere il disclaimer "progetto NON ufficiale" in README, `const.DISCLAIMER`,
  step `user` del config flow e `config.yml` degli issue template.
- Non committare token, `.env`, file di esempio/dati di stazioni.

## Comandi

```bash
# Sintassi (nessuna dipendenza richiesta)
python -m compileall custom_components/ha_rivers

# Lint (se ruff è installato: pipx install ruff)
ruff check custom_components/ha_rivers

# JSON (manifest, strings, translations)
python -c "import json,glob;[json.load(open(f)) for f in glob.glob('custom_components/ha_rivers/**/*.json',recursive=True)];print('ok')"
```

La validazione Home Assistant (`hassfest` + `hacs/action`) gira in CI
(`.github/workflows/validate.yml`) su push/PR. Prima di taggare una release:
attendere CI verde.

## Non fare

- Non ri-testare le API con curl: gli endpoint e i comportamenti verificati sono
  documentati in `docs/ARCHITECTURE.md`.
- Non introdurre una cartella `examples/` o `tests/` con dati reali: non devono
  essere pubblicati.
