# Changelog - Dadillo

Tutti i cambiamenti e le novità introdotte nelle versioni di Dadillo.

## [2.7.0] - 2026-08-19

### Aggiunto
- **Nuovo Flusso di Fine Torneo con Wizard di Premiazione Ufficiale**:
  - Quando si conclude l'ultima partita, nella classifica finale l'utente può verificare/modificare i criteri definitivi e premere il pulsante *"Avanti: Conferma Criteri e Assegna Medaglie"*.
  - Dialogo accessibile di scelta per revisionare i discepoli *"Uno per uno"* (con pulsanti *Aggiorna* e *Salta discepolo*) oppure registrarli *"Tutti in massa"*.
  - Calcolo ufficiale e irrevocabile delle medaglie basato rigidamente sulle regole e sui criteri del torneo.
  - Salvataggio immediato in `Dadillo_players.json` ed esportazione automatica di `Giocatori.txt`.
- **Unione Intelligente dei Database Giocatori con Riconoscimento Similarità (`difflib`)**:
  - Algoritmo di fuzzy matching per individuare discepoli con nomi simili (es. `Siddharta` vs `Siddharta33`, maiuscole/minuscole).
  - Dialogo interattivo accessibile per chiedere se si tratti dello stesso giocatore e consentire la scelta del nickname da mantenere.
  - Deduplicazione atomica dei singoli tornei nello storico: le medaglie e la somma dei piazzamenti vengono ricalcolati unicamente dai tornei effettivamente registrati, impedendo qualsiasi duplicazione di medaglie in caso di fusioni multiple.

---

## [2.6.2] - 2026-08-17

### Modificato
- **Ordinamento Classifiche con Metodo a Gruppi e Sottogruppi Ricorsivi (Classifica Avulsa Universale)**:
  - Sostituito il vecchio algoritmo comparativo a coppie con una funzione universale gerarchica a partizionamento di gruppo ([`rank_tournament_players`](file:///e:/git/Mine/Dadillo/standings.py#L39)).
  - Risolti i casi di parità con 3 o più giocatori (es. triangolari ciclici e mini-gironi) calcolando le statistiche dei soli scontri diretti interni al gruppo a pari merito.
  - Introdotta la risoluzione ricorsiva per sottogruppi parzialmente discriminati e la transizione automatica allo spareggio secondario o alfabetico in caso di parità globale.
  - Estesa la suite di test ([`test_standings_ranking.py`](file:///e:/git/Mine/Dadillo/test_standings_ranking.py)) con test specifici per parità a 3 e 4 giocatori, pareggi ciclici e priorità punteggio alto/basso.

---

## [2.6.1] - 2026-07-30

### Modificato
- **Miglioramento Accessibilità Selezione Giocatori DB**: Nel setup dei giocatori ([`SetupPlayersDialog`](file:///e:/git/Mine/Dadillo/dialogs.py#L190)), aggiungendo un giocatore col tasto Spazio dall'elenco del DB locale:
  - Il giocatore viene rimosso dall'elenco visibile del DB locale (evitando inserimenti duplicati).
  - L'etichetta del controllo visualizza e dichiara immediatamente agli screen reader (NVDA/JAWS) il numero di elementi rimanenti.
  - Il focus e la selezione rimangono sull'elenco DB (sull'elemento adiacente) senza saltare agli iscritti.
  - Quando l'elenco del DB locale è vuoto, il focus passa automaticamente al campo di testo per l'inserimento manuale dei nuovi iscritti.

---

## [2.6.0] - 2026-07-30

### Aggiunto
- **Criteri di Classifica Salvati per Torneo**: Ogni torneo salva in modo permanente nel proprio file JSON (`Dadillo.json`) le regole di ordinamento e spareggio (`main_criterion`, `score_direction`, `tiebreaker_1`, `tiebreaker_2`).
- **Priorità Punteggio (Alto / Basso)**: Supporto nativo ai tornei dove il punteggio più basso è migliore (es. golf, punteggi a penalità, minis). Il criterio si applica ai punti senza alterare la priorità delle vittorie.
- **Setup Avanzato Torneo**: Aggiunto un riquadro "Criteri di Classifica e Spareggi" nel dialogo di creazione del torneo ([`SetupTournamentDialog`](file:///e:/git/Mine/Dadillo/dialogs.py#L52)).
- **Salvataggio Istantaneo da Classifica (Ctrl+L)**: Qualsiasi modifica apportata ai menu a tendina nella vista della classifica aggiorna e salva automaticamente il file `.json` del torneo.
- **Suite di Test Automatizzati**: Creata la suite pytest ([`test_standings_ranking.py`](file:///e:/git/Mine/Dadillo/test_standings_ranking.py)) per verificare persistenza, priorità punteggio alto/basso, spareggi negli scontri diretti e ordinamento complessivo.

### Modificato
- Ristrutturato il pannello delle classifiche ([`StandingsPanel`](file:///e:/git/Mine/Dadillo/standings.py#L14)) per includere i controlli per la priorità del punteggio e degli spareggi.
- Aggiornata la finestra delle regole ([`SettingsDialog`](file:///e:/git/Mine/Dadillo/dialogs.py#L345)) e sincronizzati i dati tra le impostazioni generali dell'app e il torneo attivo.

---

## [2.5.0] - 2026-05-30

### Aggiunto
- **Gestione e Modifica Giocatori DB**: Menu dedicato per rinominare o eliminare discepoli dal database storico.
- **Classifica Generale della Hall of Fame**: Schermata con ordinamento flessibile per la classifica globale.
- **Inserimento Rapido da DB**: Selezione veloce dei partecipanti tramite tasto Spazio o doppio clic.
- **Unione Database Giocatori**: Funzionalità in `Opzioni -> Unisci Database Giocatori...` per fondere due file `Dadillo_players.json` da PC diversi.
- **Case-Sensitivity Nickname**: Supporto ai nickname case-sensitive senza normalizzazione automatica dei caratteri.
