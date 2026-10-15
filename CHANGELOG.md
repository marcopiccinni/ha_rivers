# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/) e il
progetto adotta il [Semantic Versioning](https://semver.org/lang/it/).

## [0.1.2] - 2026-10-15

### Changed

- Rimossi dal repository pubblicato i file di sviluppo locale (istruzioni per
  assistenti, cartella `.opencode/`); ampliato `.gitignore`.
- Nessuna modifica funzionale alle entità.

## [0.1.1] - 2026-10-15

### Added

- Entità `device_tracker` per stazione: espone la posizione fissa della
  stazione, che compare automaticamente sulla dashboard Mappa (tab
  *Dispositivi*) senza dover elencare a mano i sensori.

## [0.1.0] - 2026-10-15

### Added

- Prima release.
- Config flow con ricerca stazioni lato server su ARPAE (nome, bacino, comune,
  provincia, codice) e validazione della serie su AllertaMeteoER.
- Una voce di configurazione (e un dispositivo) per stazione.
- Sensori: livello, stato allerta derivato, soglie gialla/arancione/rossa,
  tendenza, timestamp di misura e metadati.
- Binary sensor "stazione attiva".
- Sensori extra opzionali: portata, precipitazione 1h, temperatura, umidità,
  pressione, vento (dove disponibili).
- Opzioni per intervalli di aggiornamento serie e metadati.
- Catalogo stazioni in cache (24 h) e supporto diagnostica.
