# Changelog - Dadillo

Tutti i cambiamenti e le novità introdotte nelle versioni di Dadillo.

## [2.8.2] - 2026-09-01

Correzioni del blocco 2 della revisione di fase 1, dedicato agli errori bloccanti e ai dati mostrati sbagliati. Riferimento: `analisi_codice_fase_1.txt`.

### Risolto
- **Classifica inconsultabile dopo il ritiro di un giocatore** (rilievo 1, critico):
  - Le strisce di vittorie venivano contate su dizionari costruiti con i soli partecipanti attivi, ma indicizzati con i nomi letti dalle partite giocate. Dopo aver soppresso un discepolo che aveva già vinto almeno una partita, la schermata delle classifiche si interrompeva con un errore, proprio quando il ritiro chiudeva le battaglie e portava alla premiazione.
  - Il calcolo è ora nella funzione `calculate_streaks` di [standings.py](file:///E:/git/mine/Dadillo/standings.py), che tiene conto di tutti i nomi presenti negli archivi del torneo e restituisce i soli giocatori ancora in gara.
- **Annullamento di una partita che coinvolge un ritirato** (rilievo 2, critico):
  - Premere `Canc` su una vittoria a tavolino, o su una partita disputata da chi era stato poi ritirato, interrompeva il ripristino dei punteggi a metà, lasciando i dati incoerenti.
  - Ora la condizione viene verificata prima di toccare qualsiasi statistica e l'operazione viene rifiutata con un messaggio che spiega il motivo.
- **Criterio di classifica perduto in silenzio** (rilievo 3):
  - La finestra Regole Torneo offriva "Punti Totali" mentre creazione torneo e classifica usavano "Punti": aprendo le Regole su un torneo a punti la casella restava senza selezione e la conferma salvava un criterio vuoto, facendo ricadere l'ordinamento su Vittorie senza alcun avviso.
  - Introdotto in [data.py](file:///E:/git/mine/Dadillo/data.py) il vocabolario unico `MAIN_CRITERIA`, `RANKING_VIEWS`, `TIEBREAKERS_1`, `TIEBREAKERS_2`, `DRAW_SPLITS`, usato da tutte e tre le finestre, più `normalize_main_criterion` e `normalize_choice`, che al caricamento riconoscono le vecchie etichette e recuperano i criteri già azzerati nei file salvati.
- **Durata del torneo e ritmo di gioco sbagliati di tutto il fuso orario** (rilievo 4):
  - Le date erano salvate in ora locale e rilette come se fossero UTC, mentre il momento attuale era preso in UTC reale: un torneo iniziato dieci minuti prima risultava durato 22 ore.
  - Le date e ore sono ora salvate in formato ISO completo di fuso, con `now_timestamp`, e rilette con `parse_timestamp`, che accetta anche il vecchio formato interpretandolo come ora locale. Nessun file già salvato va convertito a mano.
- **Media punti per pareggio mai calcolata** (rilievo 12):
  - La statistica confrontava il risultato con il codice `X`, che il programma non produce mai: il codice del pareggio è `3`. La riga ora compare correttamente.

### Aggiunto
- Quattro nuovi test automatici: strisce di vittorie con un giocatore ritirato, riconoscimento delle vecchie etichette del criterio principale, sopravvivenza del criterio a punti al salvataggio e rilettura, durata calcolata correttamente con i due formati di data. La suite passa da 19 a 23 test.

---

## [2.8.1] - 2026-09-01

Correzioni del blocco 1 della revisione di fase 1, dedicato alla sicurezza dei dati. Riferimento: `analisi_codice_fase_1.txt`.

### Risolto
- **Percorsi dei file di dati indipendenti dalla cartella di avvio** (rilievo 6):
  - `Dadillo.json`, `Dadillo_settings.json`, `Dadillo_players.json` e `Giocatori.txt` erano risolti rispetto alla directory di lavoro corrente. Avviando il programma da un'altra cartella non venivano più trovati e ne venivano creati di nuovi e vuoti altrove.
  - Introdotta `get_app_dir()` in [data.py](file:///E:/git/mine/Dadillo/data.py), che ricava la cartella dell'applicazione dal modulo quando si esegue da sorgente e da `sys.executable` quando si esegue l'eseguibile PyInstaller. Tutti i percorsi sono ora assoluti e costruiti con `os.path.join`.
  - `TournamentData`, `SettingsData` e `PlayerDB` accettano un parametro opzionale `base_dir`, usato dai test per lavorare su cartelle temporanee senza toccare gli archivi reali.
- **Salvataggi atomici con copia di sicurezza** (rilievo 5, prima parte):
  - Tutti i salvataggi troncavano il file di destinazione prima di scrivere: un errore a metà scrittura, un disco pieno o un file bloccato da un altro programma potevano distruggere il torneo in corso o la Hall of Fame.
  - Aggiunte `atomic_write_text` e `atomic_write_json`, che scrivono su file temporaneo nella stessa cartella, forzano i dati su disco con `os.fsync`, conservano la versione precedente in un file con estensione `.bak` e solo allora sostituiscono l'originale con `os.replace`.
  - Aggiunta l'eccezione `SaveError`, con messaggio già pronto per l'utente e organizzato in righe brevi per la lettura su display braille.
  - Al primo avvio, se il file delle impostazioni non è scrivibile, il programma parte comunque con i valori predefiniti invece di interrompersi.
  - Nuovo modulo [ui_utils.py](file:///E:/git/mine/Dadillo/ui_utils.py) con `save_or_warn`: ogni salvataggio dell'applicazione passa da qui e, se non riesce, mostra un messaggio parlante invece di far risalire l'errore. Chiudendo il programma con un salvataggio fallito viene chiesto se uscire lo stesso; il messaggio "Salvato", quello di esportazione riuscita e quello di premiazione compaiono solo a scrittura realmente avvenuta.
  - Se il salvataggio fallisce durante la rinomina o l'eliminazione di un discepolo, la modifica viene annullata anche in memoria, così il programma non resta disallineato dai dati su disco.
- **Archivi danneggiati riconosciuti invece che scambiati per assenti** (rilievo 16):
  - Il caricamento del torneo non restituiva più alcuna differenza fra file mancante e file corrotto: un `Dadillo.json` danneggiato veniva trattato come assenza di torneo e il torneo nuovo lo sovrascriveva. L'archivio dei giocatori, nello stesso caso, veniva semplicemente svuotato e il primo salvataggio cancellava la Hall of Fame.
  - Aggiunte l'eccezione `DataFileError`, la funzione `quarantine_file`, che mette da parte una copia datata del file danneggiato senza toccare l'originale, e la validazione della struttura dei dati letti (giocatori, partite giocate e non giocate).
  - All'avvio Dadillo avvisa se il torneo o l'archivio dei discepoli non sono leggibili, indicando il nome della copia messa da parte. Finché l'archivio dei discepoli resta danneggiato, salvataggio ed esportazione della Hall of Fame vengono rifiutati con un messaggio esplicito.
- **Fusione database che poteva cancellare un discepolo** (rilievo 7):
  - Unendo un database esterno, scegliere per il discepolo un nickname già appartenente a un altro giocatore locale ne sovrascriveva medagliere e storico, senza avviso e senza possibilità di recupero.
  - Ora i due storici vengono fusi sotto il nome scelto, senza duplicare i tornei già presenti, con i contatori delle medaglie ricalcolati e il dettaglio riportato nel resoconto della fusione.

### Aggiunto
- Cinque nuovi test automatici in `test_standings_ranking.py`, che coprono la scrittura atomica con copia di sicurezza, il rifiuto di un torneo danneggiato o strutturalmente non valido, la protezione dell'archivio discepoli non leggibile e la fusione senza perdita di storici. La suite passa da 14 a 19 test.

### Modificato
- I test di `test_standings_ranking.py` non usano più `os.chdir` ma il parametro `base_dir`, così non possono in nessun caso scrivere sui file di dati reali.

---

## [2.8.0] - 2026-08-20

### Aggiunto
- **Formattazione Estesa delle Date in Tutta l'Applicazione**:
  - Implementata la funzione universale `format_date_extended` con localizzazione italiana deterministica per giorni e mesi (es. `giovedì 20 agosto 2026`).
  - Formattazione estesa applicata nello storico tornei, nella Hall of Fame (`Dadillo_players.json` e `Giocatori.txt`), nelle schermate di dettaglio giocatore, nel wizard di premiazione, nella visualizzazione della classifica e nei file di salvataggio delle partite.
- **Integrazione Dati Torneo "Agostino1-4-24-Bonus"**:
  - Integrati i risultati del torneo con aggiornamento di medagliere, storico e somma piazzamenti per i 12 discepoli partecipanti nella Hall of Fame.

---

## [2.7.1] - 2026-08-19

### Risolto
- **Hotfix Auto-Updater e Dipendenze Compilazione**:
  - Inclusi esplicitamente `requests`, `urllib3`, `certifi`, `charset_normalizer` e `chardet` tra gli `hiddenimports` nel file di build ([`Dadillo.spec`](file:///E:/git/Mine/Dadillo/Dadillo.spec)).
  - Ottimizzata la chiusura immediata del processo al momento dell'aggiornamento in [Dadillo.py](file:///E:/git/Mine/Dadillo/Dadillo.py) per prevenire conflitti di file bloccati durante la sovrascrittura di `xcopy`.

---

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
