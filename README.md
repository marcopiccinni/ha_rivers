# Fiumi Emilia-Romagna (Home Assistant)

Integrazione **personalizzata (custom)** per Home Assistant che porta in HA lo
stato idrometrico dei fiumi dell'Emilia-Romagna, con una stazione per ogni voce
configurabile.

> ## ⚠️ Disclaimer
>
> Questa integrazione è **NON ufficiale** e **non è affiliata, approvata o
> supportata** da ARPAE, da AllertaMeteoER, dalla Regione Emilia-Romagna o da
> Home Assistant.
>
> I dati provengono da servizi pubblici di terze parti e vengono forniti
> **"così come sono"**, **senza alcuna garanzia**. La **disponibilità del
> servizio**, la sua **continuità** e l'**esattezza dei dati non sono
> garantite** e possono cambiare o interrompersi in qualsiasi momento senza
> preavviso. **Non utilizzare questa integrazione per decisioni di sicurezza,
> protezione civile o emergenza**: fare sempre riferimento ai canali ufficiali.

## Fonti dati

| Organizzazione | Uso | Endpoint |
| --- | --- | --- |
| **ARPAE** | metadati stazione: soglie, coordinate, bacino, variabili | `apps.arpae.it/REST/meteo_osservati` |
| **AllertaMeteoER** | serie idrometrica quasi in tempo reale | `allertameteo.regione.emilia-romagna.it/o/api/allerta` |

L'integrazione interroga i servizi online e non è affiliata a nessuno dei due.

## Installazione (HACS)

1. In HACS apri il menu **⋮ → Custom repositories**.
2. Incolla l'URL di questo repository e scegli la categoria **Integration**.
3. Cerca **Fiumi Emilia-Romagna** in HACS e premi **Download**.
4. **Riavvia** Home Assistant.

### Installazione manuale

Copia la cartella `custom_components/ha_rivers` in
`<config>/custom_components/ha_rivers` e riavvia Home Assistant.

## Configurazione

1. **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**.
2. Cerca **Fiumi Emilia-Romagna**.
3. Inserisci un testo di ricerca: nome fiume, bacino, comune, provincia o
   codice stazione (la ricerca è lato server).
4. Scegli la stazione dai risultati.
5. Ripeti l'aggiunta per **ogni stazione** desiderata: viene creata una voce di
   configurazione per stazione, con il proprio intervallo di aggiornamento.

L'integrazione verifica automaticamente che la stazione selezionata esponga
davvero una serie di livello; in caso contrario propone di sceglierne un'altra.

## Entità

Per ogni stazione viene creato un **dispositivo** con le seguenti entità:

| Entità | Descrizione | Unità |
| --- | --- | --- |
| `sensor.*_level` | Livello idrometrico (con attributi geografici e soglie) | m |
| `sensor.*_alert` | Stato allerta derivato: `normale`/`gialla`/`arancione`/`rossa`/`nd` | — |
| `sensor.*_threshold_yellow` | Soglia gialla | m |
| `sensor.*_threshold_orange` | Soglia arancione | m |
| `sensor.*_threshold_red` | Soglia rossa | m |
| `sensor.*_trend` | Tendenza del livello nell'ultima ora | m/h |
| `sensor.*_last_measurement` | Timestamp dell'ultima misura di livello | — |
| `sensor.*_last_metadata_update` | Timestamp dell'ultimo aggiornamento metadati | — |
| `binary_sensor.*_station_active` | Stazione attiva secondo AllertaMeteoER | — |

Entità **extra** (create solo se la stazione espone la variabile; alcune
disabilitate di default perché rare):

| Entità | Descrizione | Unità |
| --- | --- | --- |
| `sensor.*_discharge` | Portata istantanea | m³/s |
| `sensor.*_precipitation_1h` | Precipitazione cumulata 1h | mm |
| `sensor.*_temperature` | Temperatura 2 m | °C |
| `sensor.*_humidity` | Umidità 2 m | % |
| `sensor.*_pressure` | Pressione atmosferica | hPa |
| `sensor.*_wind_speed` | Velocità vento | — |
| `sensor.*_wind_direction` | Direzione vento | ° |

## Opzioni

Per ogni stazione (voce di configurazione → **Configura**):

- **Aggiornamento serie livello** — default `120` s.
- **Aggiornamento soglie / metadati** — default `12000` s.

I valori di default ricalcano la configurazione di riferimento. Diminuisci gli
intervalli con moderazione: i servizi sono pubblici e gratuiti.

## Migrazione dal vecchio script

Se usavi uno script esterno che faceva push via REST (`sensor.river_station_*`),
**disattivalo** dopo aver aggiunto le stazioni in questa integrazione: mantenere
entrambi produce entità duplicate. Le entità di questa integrazione sono
registrate correttamente e sopravvivono ai riavvii di Home Assistant.

## Note

- Dati e disponibilità dipendono interamente dai servizi di terze parti.
- Progetto personale, **manutenzione e supporto non garantiti**.
- Marchi e nomi citati appartengono ai rispettivi proprietari.

## Licenza

[MIT](LICENSE)
