# Dadillo - L'Altare del Sacrificio (Versione 2.13.1)

**Dadillo** è un gestore di tornei scritto in Python. Gestisce giocatori, abbinamenti, classifiche e record con una personalità... *molto devota* al suo utilizzatore.

Le versioni dalla 2.8.1 alla 2.9.1 sono il risultato della revisione completa del codice, fase 1: salvataggi che non possono più lasciare i dati a metà, archivi danneggiati riconosciuti invece che sovrascritti, classifiche riscritte per la lettura con screen reader e display braille, regole del torneo coerenti fra tutte le finestre. Dalla 2.10.0 in poi sono arrivate la modifica delle date del torneo, la finestra di aggiornamento con le note della versione la pulizia dei residui dopo un aggiornamento e, con la 2.11.2, finestre che si adattano ai caratteri grandi. La 2.11.4 riporta il fuoco dove era quando si annulla una finestra, e la 2.11.5 calcola la media piazzamenti su tutte le posizioni. Con la 2.12 la proposta di aggiornamento aspetta due minuti, e l'aggiornamento si applica anche se il messaggio finale si legge con calma. La 2.13 porta la classifica generale a punti, con gli ordinali davanti ai nomi. Il dettaglio è nel [CHANGELOG](CHANGELOG.md).

## Caratteristiche

- **Date del torneo modificabili (Novità 2.10.0)**: dal menu Opzioni, la voce "Modifica date del torneo" apre una finestra con data e ora di inizio e di fine, già compilate, nel formato giorno/mese/anno e ore:minuti. La data di fine si può lasciare vuota se il torneo è in corso. La voce resta disponibile anche a torneo concluso, e se le medaglie sono già state assegnate le nuove date vengono riscritte anche nello storico di tutti i discepoli che hanno partecipato, con `Giocatori.txt` rigenerato di conseguenza. Se la data non esiste sul calendario, o la fine viene prima dell'inizio, Dadillo lo dice con un messaggio parlante.
- **Le novità della versione sotto gli occhi (Novità 2.11.0)**: quando c'è un aggiornamento, la finestra mostra la versione disponibile, quella in uso e le note della release in un campo che si scorre e si rilegge con le frecce, con i pulsanti Aggiorna adesso e Non adesso; Escape vale come Non adesso. Fino alla 2.10.0 la domanda era un sì o no secco e le note non si vedevano da nessuna parte. Mentre scarica compare l'avviso di attesa, che prima mancava.
- **Proposta di aggiornamento a tempo (Novità 2.12.0)**: se nessuno risponde entro due minuti, la finestra dell'aggiornamento si chiude da sola come Non adesso, il programma prosegue e l'aggiornamento viene riproposto al prossimo avvio. Dalla 2.12.1 il messaggio "il programma si chiude per applicarlo" si può leggere con calma: lo script che sostituisce il programma parte solo dopo l'OK. Fino alla 2.11.5, con l'OK premuto dopo 30 secondi, l'aggiornamento non si applicava.
- **Residui puliti dopo un aggiornamento (Novità 2.11.0)**: la versione compilata, al primo avvio dopo un aggiornamento, si porta via i file che la vecchia installazione aveva lasciato indietro. Nasce da un guasto vero: dopo un aggiornamento dalla 2.7.1 o dalla 2.8.0 restava una cartella a metà che impediva il controllo degli aggiornamenti successivi.
- **Finestre che si adattano ai caratteri grandi (Novità 2.11.2)**: con i caratteri di Windows ingranditi, per esempio al 150 per cento, ogni finestra prende la misura del suo contenuto, si allarga trascinando il bordo o si ingrandisce a tutto schermo, e se non ci sta nello schermo scorre. Spostandosi col tab, il campo che riceve il focus viene sempre portato in vista. Fino alla 2.11.1 le finestre avevano una misura fissa, e con i caratteri grandi il campo del risultato e i pulsanti finivano fuori, senza modo di raggiungerli. Nella schermata delle classifiche le cinque scelte in alto vanno a capo invece di uscire dal bordo. Con lo screen reader non cambia niente: le finestre si leggono e si percorrono come prima.
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
- **Classifica generale a punti (Novità 2.13.0)**: la Hall of Fame e `Giocatori.txt` ordinano i discepoli per punti, con la posizione davanti al nome, per esempio "1° Siddharta33". Ogni torneo dà 100 punti al primo e agli altri in proporzione a quanti erano, fino all'ultimo, che ne prende 100 diviso il numero dei partecipanti: in un torneo da 17 il secondo prende 94.1 e l'ultimo 5.9. Si sommano i punti di tutti i tornei giocati. A parità di punti decidono gli ori, poi gli argenti, poi i bronzi, poi la media piazzamenti; chi resta pari su tutto divide la stessa posizione. Il numero dei partecipanti si ricava dall'archivio, contando i discepoli registrati in quel torneo. Nella finestra della Hall of Fame si può ordinare anche per media piazzamenti, per medaglie, per nome e per numero di tornei.
- **Media Piazzamenti (Modificata nella 2.11.5)**: per ogni giocatore Dadillo calcola la media delle posizioni finali di tutti i tornei disputati, podi compresi. Si legge come una posizione: 1 vuol dire sempre primo, 1.83 in media meglio del secondo posto, 7.50 a metà strada fra settimo e ottavo. Fino alla 2.11.4 contavano solo le posizioni dal quinto posto in giù, divise per tutti i tornei, e ogni podio valeva zero. Quando nessuna voce dello storico dice la posizione, la media è `non disponibile`, così un'assenza di dati non viene scambiata per un risultato eccellente.
- **Recupero Errori**: Un match inserito per sbaglio? Basta premere `Canc` nella lista dei match giocati per ripristinare i punteggi e riportarlo tra le partite aperte. Se uno dei due giocatori è stato ritirato dal torneo l'operazione viene rifiutata, spiegandone il motivo, invece di lasciare i punteggi a metà.

## Requisiti e Installazione

Serve Python 3 e la libreria `wxPython`. Tutte le dipendenze sono elencate in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Dadillo usa inoltre la libreria personale `GBUtils`, che deve stare nel percorso di Python anche per avviarlo da sorgente: dalla 2.11.4 le finestre prendono la misura e lo scorrimento da `GBwx.py`, il modulo di GBUtils per le applicazioni con le finestre. Il controllo degli aggiornamenti, che viene anch'esso da GBUtils, lavora solo nell'eseguibile compilato.

### Aggiornare dalla 2.7.0 o da una versione precedente

Fino alla 2.7.0 compresa l'aggiornamento automatico non arriva in fondo se, al momento del sì, è aperta la finestra Nuovo Torneo o quella dei giocatori: la versione vecchia non si chiude, la copia non avviene e si apre un'altra finestra della versione vecchia, che ripropone l'aggiornamento. Ogni tentativo ne aggiunge una. Il difetto sta nella versione installata e nessun pacchetto nuovo lo può aggirare; con un torneo in corso o concluso, invece, l'aggiornamento riesce. Se ti succede, aggiorna a mano:

1. Chiudi tutte le finestre di Dadillo, comprese quelle aperte dai tentativi falliti.
2. Scarica `Dadillo.zip` dall'ultima release su GitHub.
3. Nella cartella di Dadillo cancella `Dadillo.exe` e la cartella `_internal`.
4. Estrai l'archivio nella stessa cartella.

I file dei dati accanto all'eseguibile, cioè `Dadillo.json`, `Dadillo_players.json`, `Dadillo_settings.json` e `Giocatori.txt`, non vanno toccati: la versione nuova li legge così come sono.

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

## La classifica generale

La Hall of Fame e il file `Giocatori.txt` mettono in fila tutti i discepoli dell'archivio, dal migliore al peggiore, con la posizione davanti al nome: "1° Carla", "2° Bruno". Dalla 2.13.0 la classifica si fa a punti.

**Come si contano i punti.** In ogni torneo il primo prende 100 punti. Gli altri prendono punti in proporzione alla posizione e al numero dei partecipanti, fino all'ultimo, che prende 100 diviso il numero dei partecipanti. La formula è 100 per (partecipanti meno posizione più uno) diviso partecipanti. In un torneo da 10 il primo prende 100, il secondo 90, il terzo 80, e così via fino al decimo, che prende 10. In un torneo da 5 si scende di 20 in 20: 100, 80, 60, 40, 20.

**La classifica è la somma** dei punti di tutti i tornei giocati. Quindi contano due cose: dove sei arrivato rispetto a quanti eravate, e quanti tornei hai giocato, perché ognuno porta qualcosa, anche arrivando ultimi.

**Un esempio.** Due tornei: il torneo A con 10 partecipanti, il torneo B con 5.
- Anna vince il torneo A, 100 punti, e arriva quarta nel B, 40 punti: in tutto 140.
- Bruno arriva secondo nel torneo A, 90 punti, e secondo nel B, 80 punti: in tutto 170.
- Carla arriva terza nel torneo A, 80 punti, e vince il B, 100 punti: in tutto 180.
- Dario gioca solo il torneo A e arriva quinto: 60 punti.

La classifica generale è: 1° Carla con 180, 2° Bruno con 170, 3° Anna con 140, 4° Dario con 60. Bruno, con due secondi posti, sta davanti ad Anna, che ha un oro ma anche un quarto posto: la costanza conta quanto il colpo singolo. Si vede anche perché conta il numero dei partecipanti: il secondo posto di Bruno vale 90 nel torneo da 10 e 80 in quello da 5, perché nel primo ha lasciato dietro di sé otto avversari, nel secondo tre.

**A parità di punti** decide chi ha più ori, poi più argenti, poi più bronzi, poi la media piazzamenti più bassa. Chi resta pari su tutto divide la stessa posizione: due discepoli al 3°, e il successivo al 5°.

**Da dove viene il numero dei partecipanti.** Lo storico di un discepolo non lo scrive: Dadillo lo ricava contando nell'archivio i discepoli registrati in quel torneo, con lo stesso titolo e la stessa data d'inizio. Per questo conviene registrare alla premiazione tutti i partecipanti, anche gli ultimi: se nella revisione uno per uno salti qualcuno, il torneo risulta più piccolo e i punti degli altri cambiano. Il numero non scende comunque mai sotto il piazzamento più basso registrato.

**Altri ordinamenti.** Nella finestra della Hall of Fame, con Ordina per, si può mettere in fila l'archivio anche per media piazzamenti, per ori, argenti, bronzi e legni, per nome e per numero di tornei, in un verso o nell'altro. Fino alla 2.12.1 l'ordine predefinito era il medagliere, dove un oro stava davanti a qualunque numero di argenti.

## File usati da Dadillo

Vivono tutti nella cartella dell'applicazione.

- `Dadillo.json`: il torneo in corso, con giocatori, partite e regole.
- `Dadillo_settings.json`: le tue impostazioni generali, valide per i tornei futuri.
- `Dadillo_players.json`: l'archivio storico dei discepoli, medagliere e partecipazioni.
- `Giocatori.txt`: la Hall of Fame in forma leggibile, rigenerata a ogni variazione dello storico e ricreabile in qualsiasi momento dal menu Giocatori.
- I file con estensione `.bak` sono le copie della versione precedente, create in automatico per il torneo e per l'archivio dei discepoli.

## Autori e Riconoscimenti

Creato e ideato da **Gabriele Battaglia (IZ4APU)**.

Hanno contribuito o fornito supporto: Bersan Vrioni, Marco De Paoli, Emanuela Pontiroli, Stella Gemini e ClaudIA (Claude Opus 5 e Opus 5.5), che hanno curato la logica, la GUI e l'accessibilità.

## Licenza

Questo progetto è distribuito sotto licenza **GPL-3.0**. Vedi il file [LICENSE](LICENSE) per i dettagli.
