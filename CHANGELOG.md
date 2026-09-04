# Changelog - Dadillo

Tutti i cambiamenti e le novità introdotte nelle versioni di Dadillo.

## [2.10.0] - 2026-09-04

Richiesta accolta dalla issue 3 del repository, piu' l'allineamento all'ambiente nuovo.

### Aggiunto
- **Modifica delle date del torneo** (issue 3): nuova voce "Modifica date del torneo" nel menu Opzioni, accanto a Regole Torneo. Apre una finestra con quattro campi, data e ora di inizio e data e ora di fine, gia' compilati con i valori registrati e con il formato dichiarato nell'etichetta, giorno/mese/anno e ore:minuti. La data di fine si puo' lasciare vuota se il torneo e' ancora in corso.
- La voce resta disponibile per tutta la vita del torneo, anche a battaglie concluse. **Se il torneo e' gia' stato premiato, le nuove date vengono riscritte anche nello storico di tutti i discepoli che vi hanno partecipato**, e il file `Giocatori.txt` viene rigenerato: le voci gia' registrate porterebbero altrimenti le date vecchie.
- I controlli avvisano con un messaggio parlante se la data non e' nel formato giusto, se non esiste sul calendario o se la fine viene prima dell'inizio.
- Tre nuovi test automatici: conversione fra i campi scritti a mano e il timestamp con fuso, aggiornamento mirato dello storico dei soli partecipanti, comportamento della finestra con torneo concluso e con torneo in corso. La suite passa da 31 a 34 test.

### Modificato
- Verificato il funzionamento con **Python 3.14.5** e wxPython 4.3.1: prove, validatore, compilazione, eseguibile e archivio di distribuzione.
- `zip_maker.py` usa ora `crea_archivio_release` di GBUtils V93, quindi la regola sulle esclusioni e' una sola per tutto il parco software. Chiude per Dadillo la nota 7 di `fix_da_fare.txt`.

---

## [2.9.1] - 2026-09-02

Pubblicata su GitHub il 2026-09-02 come release `v2.9.1`, con il solo archivio `Dadillo.zip` in allegato. Verificato che l'auto updater la riconosca e ne riceva le note.

Chiusura del secondo giro di collaudo della fase 1. Riferimento: `collaudo.txt` e sezione 7 di `analisi_codice_fase_1.txt`.

### Risolto
- **L'assenza di GBUtils non impedisce più l'avvio**: se la libreria dell'aggiornatore non è raggiungibile, l'eseguibile parte comunque senza controllo aggiornamenti, invece di chiudersi in silenzio, dato che non ha una console dove mostrare l'errore.
- **Classifica di un torneo concluso aperta con Ctrl+L** (collaudo, prova 26): veniva sempre presentata come parziale, quindi mostrava l'intestazione "Classifica parziale", le partite giocate su ogni riga, `G6/6`, e la durata marcata come provvisoria, anche a torneo finito. Il contenuto della schermata dipende ora dallo stato del torneo, cioè dal fatto che non ci siano più partite da giocare, mentre il parametro `is_final` decide soltanto quale pulsante compare in fondo. Difetto precedente a questa revisione, emerso solo con la classifica a riga singola.

### Aggiunto
- Test automatico che verifica entrambi i casi: torneo concluso aperto con Ctrl+L, senza giocate né dicitura provvisoria, e torneo ancora in corso, con le giocate al loro posto. La suite passa da 30 a 31 test.

### Modificato
- **Pacchetto di distribuzione a norma**: `zip_maker.py` è stato riscritto sul modello collaudato di Orologic, come indicato nelle note di GBUtils. Ora esclude dall'archivio i file personali che nascono provando l'eseguibile, cioè torneo, impostazioni, archivio dei discepoli, Hall of Fame, copie `.bak` e file messi in quarantena, ma applica il filtro solo accanto all'eseguibile e mai dentro `_internal`, dove serve tutto quello che ha messo PyInstaller, `base_library.zip` compreso. Prima Dadillo non escludeva nulla e i dati di chi compilava finivano nel pacchetto pubblico.
- **File di build più esplicito**: dichiarata in `pathex` la posizione di GBUtils, che non è un pacchetto installato ma una cartella accanto al progetto, così la compilazione non dipende più dal `PYTHONPATH` della macchina; ampliato l'elenco delle librerie escluse e commentato il motivo di ogni sezione.
- **Manuale aggiornato**: il README descrive ora la classifica a riga singola con la sua legenda, i salvataggi sicuri e il riconoscimento degli archivi danneggiati, la scelta del comportamento della ricerca, le parità dichiarate, la richiesta prima di applicare nuove regole al torneo in corso, la terza via "Non ora, rimando" nella premiazione e il significato preciso della Media Piazzamenti. Aggiunto anche l'elenco dei file usati dal programma e corretta l'installazione, che ora passa da `requirements.txt` e dal file di build incluso.

---

## [2.9.0] - 2026-09-02

Interventi nati dal collaudo sul campo della fase 1, compilato da Gabriele. Riferimento: `collaudo.txt` e sezione 7 di `analisi_codice_fase_1.txt`.

### Aggiunto
- **Scelta del comportamento della ricerca per due nomi** (collaudo, prova 20): nuova voce in Opzioni, Regole Torneo, "Cercando due nomi nelle liste delle partite", con due modi, coppia in qualsiasi ordine, che resta il predefinito, e primo nome poi secondo. La scelta è permanente, salvata in `Dadillo_settings.json`, e vale allo stesso modo per la lista delle partite giocate e per quella delle non giocate.

### Modificato
- **Classifica su una riga sola per giocatore** (collaudo, prova 17): al posto delle due righe, ogni discepolo occupa ora una riga con una lettera davanti a ogni valore, `1. Marco, oro. T12 V4 P0 S2`, e la legenda subito sopra spiega le lettere, `punti(T), vittorie(V), pareggi(P), sconfitte(S)`. Le partite giocate compaiono, come `G6/7`, solo nella classifica parziale: a torneo concluso sarebbero sempre tutte. Le righe scendono da circa 43 a circa 30 caratteri.
- **Niente copia di sicurezza per `Giocatori.txt`** (collaudo, prova 16): è un file derivato, rigenerato a ogni variazione dello storico e ricreabile con Esporta Hall of Fame, quindi non lascia più un `.bak` accanto a sé. Le copie di sicurezza restano per `Dadillo.json` e `Dadillo_players.json`, che contengono dati non ricostruibili.

### Risolto
- **Esc non chiudeva la finestra di premiazione** (collaudo, prova 10): la finestra "Destino della Hall of Fame" non aveva un pulsante di annullamento, quindi wxPython ignorava Esc e l'unica via era scegliere una delle due modalità. Ora c'è il pulsante "Non ora, rimando" ed Esc funziona.

---

## [2.8.4] - 2026-09-02

Correzioni dei blocchi 4 e 5 della revisione di fase 1: coerenza delle regole del torneo, pulizia e manutenzione. Riferimento: `analisi_codice_fase_1.txt`.

### Risolto
- **Regola dei pareggi presa dal torneo, non dalle impostazioni generali** (rilievo 11): ogni torneo salva la propria regola, ma il calcolo usava sempre quella globale, così cambiare le impostazioni alterava a posteriori i punti dei tornei vecchi.
- **Una sola regola per ricostruire i punti delle partite vecchie** (rilievo 13): classifica e annullamento partita ne applicavano due diverse allo stesso record. Ora c'è `split_match_points` in [data.py](file:///E:/git/mine/Dadillo/data.py), e le partite del vecchio formato a quattro elementi vengono convertite una volta sola al caricamento (rilievo 34), con la regola del torneo.
- **Chiudere la finestra di premiazione non assegna più le medaglie** (rilievo 14): l'uscita con Esc valeva come "tutti in massa" e registrava tutto su disco. Ora annulla.
- **Controllo dei doppioni nello storico più preciso** (rilievo 15): il confronto avveniva per sottostringa, quindi un titolo breve o ricorrente poteva far scartare un torneo nuovo. Ora titolo e data di inizio si confrontano per intero.
- **Parità irrisolte segnalate** (rilievo 21): quando nessuno spareggio riesce a separare due discepoli, la classifica lo dice, il dialogo di revisione lo ripete e, se la parità tocca le prime quattro posizioni, viene chiesta conferma prima di assegnare medaglie decise dall'ordine alfabetico.
- **Le Regole non cambiano più il torneo in corso senza chiedere** (rilievo 22).
- **Media piazzamenti onesta** (rilievo 19): chi ha solo podi viene indicato come tale e resta in cima, mentre uno storico non interpretabile non produce più uno zero che scavalcava chi ha piazzamenti veri. L'ordinamento della Hall of Fame esistente resta identico, verificato sul database reale.
- **Un solo archivio dei discepoli in memoria** (rilievo 17): sette istanze separate rileggevano il file e potevano sovrascriversi a vicenda. Ora la finestra principale ne crea uno e lo passa alle altre.
- **GBUtils importato solo quando serve** (rilievo 18): il controllo su `sys.frozen` viene prima dell'importazione, così da sorgente il programma parte anche dove GBUtils non è installato.
- **Ricerca per coppia di nomi in entrambi gli ordini** (rilievo 36): prima la partita di ritorno non veniva trovata.

### Modificato
- Rimossi i quattro parametri booleani inutilizzati da `add_or_update_player` (rilievo 23) e i campi `records_high` e `records_low`, scritti e mai usati (rilievo 25).
- Le liste delle partite si aggiornano una per volta invece che entrambe a ogni carattere digitato nella ricerca (rilievo 35).
- Intestazione autori in tutti i moduli e in `version.py`, nel formato Gabriele Battaglia (IZ4APU) & ClaudIA con modello e modalità (rilievo 26).
- Tolto il messaggio di benvenuto stampato su una console che l'eseguibile non ha (rilievo 28); reso indipendente dalla lunghezza il messaggio di nome troppo corto (rilievo 38).
- `zip_maker.py` costruisce i percorsi a partire dal proprio file (rilievo 31).

### Aggiunto
- `ruff.toml` con le regole scelte per il progetto e le eccezioni motivate (rilievo 32) e `requirements.txt` con le dipendenze (rilievo 33).
- Ripristinati in `Dadillo.spec` gli `hiddenimports` necessari all'aggiornatore, e il file è ora sotto controllo di versione invece di essere ignorato (rilievo 9).
- Sei nuovi test: regola unica dei pareggi, migrazione dei record partita, segnalazione delle parità, media piazzamenti nei casi senza dati, ricerca simmetrica della coppia, doppioni con titoli simili. La suite passa da 24 a 30 test.

### Rimosso
- `test_dialog.py` e `test_dialog2.py`, script di prova interattivi che pytest raccoglieva come test (rilievo 29).
- `agostino.txt` spostato nella cartella `materiali`, perché è un appunto di lavoro e non codice (rilievo 30).

---

## [2.8.3] - 2026-09-02

Correzioni del blocco 3 della revisione di fase 1, dedicato all'accessibilità. Riferimento: `analisi_codice_fase_1.txt`.

### Modificato
- **Classifica e Hall of Fame in forma discorsiva** (rilievo 8):
  - Eliminati tutti e nove i separatori grafici a trattini, che lo screen reader leggeva come lunghe sequenze di segni, e le tabelle a colonne allineate, in cui il significato di ogni numero dipendeva dalla posizione.
  - Ogni giocatore occupa ora righe brevi con l'etichetta accanto al dato: `1. Marco, oro. Punti 12.` seguito da `Giocate 6 su 6, vinte 4, pari 0, perse 2.` Le stesse regole valgono per la classifica generale della Hall of Fame e per i file esportati con `File, Salva lista`.
  - I riferimenti alle partite nei record sono discorsivi: `Marco, partita 4, Marco contro Selene157` al posto della forma con parentesi e barre.
  - Corretto il plurale nei punteggi: `1 punto` invece di `1 punti`.
- **Medaglie in solo testo** (rilievo 24): oro, argento, bronzo e legno non sono più accompagnati da emoji, che venivano annunciate in modo diverso a seconda della versione dello screen reader e delle sue impostazioni.
- **Righe vuote di separazione eliminate** (rilievo 37): in classifica, dettagli discepolo, resoconto della fusione, `Giocatori.txt` e liste partite esportate. Riscritti su righe brevi anche i messaggi dei dialoghi di premiazione, di somiglianza dei nickname, di conferma eliminazione e di aggiornamento disponibile.
- Tolto il segno più forzato da deviazione standard, varianza, escursione, mediane e moda, che lo screen reader annunciava come "più" davanti a grandezze sempre positive.

### Risolto
- **Focus spostato due volte dopo l'inserimento di un discepolo** (rilievo 20):
  - Due temporizzatori a 300 e 600 millisecondi spostavano il focus prima sulla lista e poi sul campo del nome, producendo annunci sovrapposti e potendo far finire i primi caratteri digitati nel controllo sbagliato.
  - Ora il focus resta nel campo del nome dopo un inserimento e nell'elenco dei partecipanti dopo una soppressione, con la selezione già posizionata sulla voce successiva.
- **Invio che poteva saltare la validazione del nome** (rilievo 10):
  - Nella finestra di aggiunta giocatore, Invio inoltrava al dialogo un evento del pulsante, aggirando la validazione agganciata al pulsante stesso: si poteva accettare un nome troppo corto o duplicato, o incorrere in un errore di attributo mancante.
  - Invio e pulsante passano ora entrambi per la stessa funzione di conferma, che chiude la finestra solo a nome valido e riporta il focus sul campo in caso di errore.

### Aggiunto
- Test automatico che verifica l'assenza di separatori grafici, righe vuote ed emoji nella classifica e la presenza delle etichette accanto ai dati. La suite passa da 23 a 24 test.

---

## [2.8.2] - 2026-09-02

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

## [2.8.1] - 2026-09-02

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
