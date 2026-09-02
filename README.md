# Dadillo - L'Altare del Sacrificio (Versione 2.9.1)

**Dadillo** è un gestore di tornei scritto in Python. Gestisce giocatori, abbinamenti, classifiche e record con una personalità... *molto devota* al suo utilizzatore.

Le versioni dalla 2.8.1 alla 2.9.1 sono il risultato della revisione completa del codice, fase 1: salvataggi che non possono più lasciare i dati a metà, archivi danneggiati riconosciuti invece che sovrascritti, classifiche riscritte per la lettura con screen reader e display braille, regole del torneo coerenti fra tutte le finestre. Il dettaglio è nel [CHANGELOG](CHANGELOG.md) e nel rapporto `analisi_codice_fase_1.txt`.

## Caratteristiche

- **Interfaccia Grafica**: Liste interattive, finestre di dialogo chiare e complete di supporto screen reader (NVDA/Jaws).
- **Classifica leggibile a colpo d'orecchio (Novità 2.9.0)**: Ogni giocatore occupa una riga sola, con una lettera davanti a ogni valore e la legenda subito sopra: `1. Marco, oro. T12 V4 P0 S2`, dove T sono i punti, V le vittorie, P i pareggi e S le sconfitte. Nella classifica parziale compare anche G, le partite giocate su quelle totali. Nessun separatore grafico, nessuna riga vuota, nessuna emoji: le medaglie sono scritte per esteso come oro, argento, bronzo e legno.
- **Gestione Tornei Round Robin**: Calcola automaticamente gli abbinamenti di andata e ritorno o solo andata.
- **Criteri di Classifica e Spareggi per Torneo**: Ogni torneo salva nel proprio file JSON le regole di ordinamento e di spareggio, compresa la regola di ripartizione dei punti in caso di pareggio. Supportata la scelta tra "Punteggio più alto" e "Punteggio più basso" (ideale per tornei a penalità, golf, minis) preservando l'ordinamento naturale delle vittorie.
- **Parità dichiarate (Novità 2.8.4)**: Quando nessuno spareggio riesce a separare due discepoli, la classifica lo dice apertamente e la posizione finale, decisa dall'ordine alfabetico, non passa più inosservata. Se la parità tocca le prime quattro posizioni, prima della premiazione viene chiesta conferma.
- **Regole del torneo in corso al riparo (Novità 2.8.4)**: Cambiando le regole dal menu Opzioni ti viene chiesto se applicarle anche al torneo già avviato, avvisandoti che la classifica potrebbe cambiare. I tornei futuri le adottano comunque.
- **Salvataggio Istantaneo**: Qualsiasi variazione ai criteri apportata nella schermata delle classifiche (Ctrl+L) viene subito registrata nel file `.json` del torneo e riflessa nell'esportazione testo.
- **Salvataggi sicuri (Novità 2.8.1)**: Ogni scrittura passa da un file temporaneo e sostituisce l'originale solo a operazione riuscita, conservando la versione precedente in un file con estensione `.bak`. Se il salvataggio non riesce, per esempio perché il file è aperto in un altro programma, Dadillo lo dice con un messaggio comprensibile invece di lasciarti credere che sia andato tutto bene.
- **Archivi danneggiati riconosciuti (Novità 2.8.1)**: Se `Dadillo.json` o `Dadillo_players.json` esistono ma non sono leggibili, Dadillo avvisa all'avvio, ne mette da parte una copia datata e si rifiuta di sovrascriverli. Un archivio rovinato non viene più scambiato per un archivio assente.
- **Dati sempre accanto al programma (Novità 2.8.1)**: Torneo, impostazioni e Hall of Fame vivono nella cartella dell'applicazione, non in quella da cui viene lanciata: Dadillo ritrova i tuoi archivi da qualunque posto lo avvii.
- **Opzioni Personalizzabili**: Decidi tu come spartire i punti in caso di pareggio (Manuale, Metà ciascuno, Nessun punto, Punti pieni a entrambi) e imposta i punteggi predefiniti di vittoria, pareggio e sconfitta.
- **Ricerca a tua misura (Novità 2.9.0)**: Nelle liste delle partite puoi cercare un termine qualsiasi oppure due nomi. Dal menu Opzioni scegli se la coppia va trovata in qualsiasi ordine, e quindi anche nella partita di ritorno, oppure solo nell'ordine in cui la scrivi. La scelta resta memorizzata e vale per entrambe le liste.
- **Hall of Fame**: Un database storico testuale (`Giocatori.txt`) e strutturato (`Dadillo_players.json`) che tiene traccia per sempre del medagliere globale (Ori, Argenti, Bronzi e Legni) e di tutte le partecipazioni dei tuoi discepoli.
- **Unione Database Asincrona**: Giocate a turno su PC diversi? Puoi unire il database dei giocatori di un amico al tuo dal menu "Opzioni, Unisci Database Giocatori", con riconoscimento dei nickname simili e resoconto dettagliato. Se il nome che scegli appartiene già a un altro discepolo, i due storici vengono fusi senza perdere nulla, mai sovrascritti.
- **Gestione e Modifica Giocatori DB**: Un menu "Giocatori" dedicato per visualizzare lo storico dettagliato di ogni discepolo, rinominarlo (con propagazione in cascata su classifiche e partite del torneo in corso) o eliminarlo definitivamente dal database.
- **Classifica Generale della Hall of Fame**: Visualizzazione e ordinamento flessibile della classifica globale, ordinabile per Nome, Ori, Argenti, Bronzi, Legni o Numero Tornei.
- **Inserimento Rapido da DB**: Durante il setup del torneo puoi selezionare i partecipanti dal database storico con lo Spazio o il doppio clic, mantenendo comunque l'editor di testo per i nuovi iscritti.
- **Case-Sensitivity per i Nickname**: Nessuna normalizzazione automatica dei caratteri, per rispettare i nickname originali case-sensitive usati su DiceWorld.
- **Performance Score**: Dadillo calcola una "Media Piazzamenti" per ogni giocatore, sommando le posizioni fuori dal podio e dividendole per tutti i tornei disputati: chi gioca molto viene premiato. Dalla 2.8.4 la media distingue i casi particolari, indicando `solo podi` per chi non ha mai chiuso oltre il quarto posto e `non disponibile` quando lo storico non è interpretabile, così un'assenza di dati non viene più scambiata per un risultato eccellente.
- **Recupero Errori**: Un match inserito per sbaglio? Basta premere `Canc` nella lista dei match giocati per ripristinare i punteggi e riportarlo tra le partite aperte. Se uno dei due giocatori è stato ritirato dal torneo l'operazione viene rifiutata, spiegandone il motivo, invece di lasciare i punteggi a metà.

## Requisiti e Installazione

Serve Python 3 e la libreria `wxPython`. Tutte le dipendenze sono elencate in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Dadillo usa inoltre la libreria personale `GBUtils` per il controllo degli aggiornamenti, che serve solo all'eseguibile compilato: da sorgente il programma parte anche senza.

## Avvio

Avvia l'app semplicemente eseguendo:

```bash
python Dadillo.py
```

*(Nota: all'apertura, per gli utenti screen reader, la finestra parte ingrandita e il focus viene sempre portato dove serve.)*

Se preferisci un eseguibile, compila con `pyinstaller` usando il file di build incluso, che contiene già le dipendenze necessarie all'aggiornatore:

```bash
pyinstaller Dadillo.spec
```

## Funzionamento

- **Fase 1: Creazione**: Fornisci il nome del torneo, l'Editto, la tipologia di girone, i punteggi predefiniti e imposta i criteri di classifica e di spareggio (Vittorie o Punti, priorità punteggio alto o basso, primo e secondo spareggio).
- **Fase 2: Le Battaglie**: La finestra principale si divide in due. A sinistra le partite da giocare, a destra quelle completate. Fai doppio clic, o premi Invio, su una partita non giocata per decretarne l'esito. Usa le caselle di ricerca per filtrare le sfide di un giocatore o di una coppia.
- **Fase 3: Conclusione del Torneo e Premiazioni**:
  1. **Apertura Classifica Finale**: Non appena l'ultima partita viene disputata, o se l'app viene avviata con un torneo già completato, Dadillo registra l'orario di fine e apre la Classifica Finale.
  2. **Verifica dei Criteri**: Nella parte superiore puoi verificare o regolare i criteri ufficiali del torneo (*Ordina per*, *Priorità Punteggio*, *primo e secondo spareggio*).
  3. **Pulsante "Avanti"**: Quando i criteri sono quelli desiderati, attiva **"Avanti: Conferma Criteri e Assegna Medaglie"** in basso. Se restano parità non risolte nelle prime quattro posizioni, Dadillo te lo dice e chiede conferma.
  4. **Scelta della Modalità di Revisione**: Si apre la finestra *"Destino della Hall of Fame"*, con tre possibilità:
     - **Uno per uno**: una finestra per ciascun discepolo con la posizione conquistata e la medaglia. Per ognuno puoi premere **"Sì, Aggiorna Discepolo!"** oppure **"Salta Discepolo"**.
     - **Tutti in massa**: registra all'istante medaglie e piazzamenti di tutti i partecipanti.
     - **Non ora, rimando**: chiude senza registrare nulla, e il pulsante Avanti resta disponibile per riprovare più tardi. Lo stesso effetto si ottiene con Esc.
  5. **Salvataggio ed Esportazione Automatica**: Al termine i risultati vengono salvati in `Dadillo_players.json` e il file testuale `Giocatori.txt` viene rigenerato. Se il salvataggio non riesce, le medaglie non vengono date per assegnate: Dadillo lo dice e puoi ritentare.
  6. **Consultazione Continua**: Il torneo concluso resta a video e consultabile per statistiche e filtri fino alla creazione di un nuovo torneo dal menu `File, Nuovo Torneo`.
- **Menu dell'App**: Dal menu in alto puoi iniziare un Nuovo Torneo, Salvare, esportare le liste delle partite, aggiungere giocatori in corsa, ritirare un giocatore, modificare le Regole del Torneo, gestire i discepoli in archivio e unire database esterni.

## File usati da Dadillo

Vivono tutti nella cartella dell'applicazione.

- `Dadillo.json`: il torneo in corso, con giocatori, partite e regole.
- `Dadillo_settings.json`: le tue impostazioni generali, valide per i tornei futuri.
- `Dadillo_players.json`: l'archivio storico dei discepoli, medagliere e partecipazioni.
- `Giocatori.txt`: la Hall of Fame in forma leggibile, rigenerata a ogni variazione dello storico e ricreabile in qualsiasi momento dal menu Giocatori.
- I file con estensione `.bak` sono le copie della versione precedente, create in automatico per il torneo e per l'archivio dei discepoli.

## Autori e Riconoscimenti

Creato e ideato da **Gabriele Battaglia (IZ4APU)**.

Hanno contribuito o fornito supporto: Bersan Vrioni, Marco De Paoli, Emanuela Pontiroli, Stella Gemini e ClaudIA (Claude Opus 5), che hanno curato la logica, la GUI e l'accessibilità.

## Licenza

Questo progetto è distribuito sotto licenza **GPL-3.0**. Vedi il file [LICENSE](LICENSE) per i dettagli.
