# Architettura e API (riferimento verificato)

Documento di riferimento per sviluppatori. **Tutti i comportamenti qui
descritti sono stati verificati dal vivo**: non è necessario riprovare le API.

## Due organizzazioni, un codice stazione

I codici stazione coincidono tra le due fonti (verificato: intersezione
251/304 tra le stazioni idro ARPAE e le 618 di AllertaMeteoER). Si usa quindi
un unico `station_id`.

### ARPAE — `https://apps.arpae.it/REST/meteo_osservati/`

API stile Eve (Flask). Query params usati:

- `where` — filtro MongoDB-like, JSON serializzato.
  - Solo stazioni con livello idro:
    `{"anagrafica.variabili":"livello_idro"}` → **304 stazioni**.
  - Ricerca testuale server-side (case-insensitive substring):
    `{"anagrafica.variabili":"livello_idro","$or":[{"anagrafica.nome":{"$regex":Q,"$options":"i"}},{"anagrafica.bacino":...},{"anagrafica.comune":...},{"anagrafica.provincia":...},{"_id":Q}]}`
  - Singola stazione: `{"_id":"<id>"}` con `max_results=1`.
- `projection` — **funziona**: `{"dati":0}` rimuove la serie storica `dati`
  (record da ~1 KB invece di ~30 KB). Usata nel catalogo e nelle ricerche.
- `max_results` — es. 500 per il catalogo; paginazione via `_meta.total`.

Campi utili per record: `_id`, `_updated` (HTTP date, es.
`Thu, 15 Oct 2026 10:48:09 GMT`), `anagrafica.{nome,bacino,sottobacino,comune,provincia,regione,altitudine,cod_istat,proprietario,gestore,variabili,geometry.coordinates[lng,lat],sensori.livello_idro.soglie[gialla,arancione,rossa]}`, `dati.{YYYYMMDD}.{HHMM}.{variabile}`.

Variabili osservate (304 stazioni idro): `livello_idro` (304),
`precipitazione_cumulata_1h` (69), `portata_istantanea` (7),
`temperatura_istantanea_2m` (22), `umidita_istantanea_2m` (11), vento,
`pressione_atmosferica` (2). `soglie` non tutte nulle in **225/304**.

L'ultimo valore di ogni variabile è in `dati[giorno_max][ora_max]` (dict
variabile→valore), usato per i sensori extra.

### AllertaMeteoER — `https://allertameteo.regione.emilia-romagna.it/o/api/allerta`

- `get-stations` → **618** stazioni: `{id_, name, municipality, lon, lat,
  attivo, height}` (lon/lat interi ÷ 1e5). ~80 KB.
- `get-time-series/?stazione=<id>&variabile=254,0,0/1,-,-,-/B13215` →
  lista `[{t (ms epoch), v}]`. Lista **vuota** `[]` se la stazione non espone
  dati → va usata per validare la selezione.
- Altri endpoint provati e **404**: `get-alerts`, `get-variabili`, `get-zones`,
  ... Non riprovare.

Header `User-Agent` inviato: alcuni percorsi fuori da `/o/api` rispondono 403.

## Flusso dati

1. **Config flow** (`config_flow.py`): query → `catalog.async_search` (ARPAE
   `$regex` + flag `attivo` da `get-stations`, entrambi in cache 24 h in
   `hass.data[DOMAIN]["catalog"]`) → selezione → `async_fetch_time_series` per
   validare → crea entry con `unique_id = station_id` (una entry per stazione).
2. **Coordinator** (`coordinator.py`): ad ogni ciclo (default 120 s) fetch serie;
   fetch metadati ARPAE (con `dati`) solo se più vecchi di `metadata_interval`
   (default 12000 s). Calcola `level` (ultimo punto), `trend` (Δ ultima ora),
   `alert` confrontando `level` con `soglie` (se una soglia è `None` → `nd`).
3. **Entità** (`sensor.py`, `binary_sensor.py`, `device_tracker.py`):
   descrizioni per livello, allerta, 3 soglie, trend, timestamp; extra creati
   solo se la variabile è in `station.variables`. Il `device_tracker` espone la
   posizione fissa (`latitude`/`longitude` da ARPAE `geometry`) e appare
   automaticamente sulla dashboard Mappa (tab *Dispositivi*).

## Default (in `const.py`)

| Costante | Valore | Note |
| --- | --- | --- |
| `DEFAULT_SCAN_INTERVAL` | 120 s | serie livello |
| `DEFAULT_METADATA_INTERVAL` | 12000 s | soglie/geo/extra |
| `CATALOG_TTL` | 24 h | cache catalogo |
| `LEVEL_VARIABLE` | `254,0,0/1,-,-,-/B13215` | variabile livello AllertaMeteoER |

## Invarianti

- Una config entry = una stazione (`unique_id` = `station_id`).
- Un dispositivo per stazione; `unique_id` entità = `<station_id>_<key>`.
- Se la serie è vuota in config flow → errore `no_series_data` (nessuna entry).
- Il servizio è di terzi: nessuna garanzia di disponibilità (vedi disclaimer).
