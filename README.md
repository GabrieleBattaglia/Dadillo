# Dadillo - L'Altare del Sacrificio (Versione 2.6.2)

**Dadillo** è un gestore di tornei scritto in Python. Gestisce giocatori, abbinamenti, classifiche e record con una personalità... *molto devota* al suo utilizzatore.
La versione 2.6.2 introduce l'algoritmo di ordinamento universale a gruppi e sottogruppi ricorsivi (classifica avulsa), risolvendo in modo matematicamente rigoroso le parità con 3 o più giocatori, triangolari ciclici e mini-gironi.


## Caratteristiche
- **Interfaccia Grafica**: Liste interattive, finestre di dialogo chiare e complete di supporto screen reader (NVDA/Jaws).
- **Miglioramento Accessibilità Selezione Giocatori DB (Novità 2.6.1)**: Selezione fluida dei discepoli dal DB con Spazio, mantenendo il focus nella lista, aggiornando dinamicamente il conteggio e nascondendo i giocatori già aggiunti per evitare duplicati.
- **Gestione Tornei Round Robin**: Calcola automaticamente gli abbinamenti di andata e ritorno o solo andata.
- **Criteri di Classifica e Spareggi per Torneo (Novità 2.6.0)**: Ogni torneo salva nel proprio file JSON le regole di ordinamento e di spareggio. Supportata la scelta tra "Punteggio più alto" e "Punteggio più basso" (ideale per tornei a penalità/golf/minis) preservando l'ordinamento naturale delle vittorie.
- **Salvataggio Istantaneo (Novità 2.6.0)**: Qualsiasi variazione ai criteri di classifica apportata nella schermata delle classifiche (Ctrl+L) viene immediatamente registrata e salvata nel file `.json` del torneo e riflessa nell'esportazione testo.
- **Opzioni Personalizzabili**: Decidi tu come spartire i punti in caso di pareggio (Manuale, Metà ciascuno, Nessun punto, ecc.) e imposta i punteggi predefiniti di vittoria/pareggio/sconfitta.
- **Hall of Fame**: Un database storico testuale (`Giocatori.txt`) e strutturato (`Dadillo_players.json`) che tiene traccia per sempre del medagliere globale (Ori, Argenti, Bronzi e Legni) e di tutte le partecipazioni dei tuoi discepoli.
- **Unione Database Asincrona**: Giocate a turno su PC diversi? Puoi unire intelligentemente il database dei giocatori (`Dadillo_players.json`) di un amico al tuo dal menu "Opzioni -> Unisci Database Giocatori...", con resoconto dettagliato di tutte le medaglie e partecipazioni fuse senza duplicati.
- **Gestione e Modifica Giocatori DB**: Un menu "Giocatori" dedicato per visualizzare lo storico dettagliato di ogni discepolo, rinominarlo (con propagazione in cascata su classifiche e partite del torneo in corso) o eliminarlo definitivamente dal database.
- **Classifica Generale della Hall of Fame**: Visualizzazione e ordinamento flessibile della classifica globale dei giocatori ordinabile per Nome, Ori, Argenti, Bronzi, Legni o Numero Tornei.
- **Inserimento Rapido da DB**: Durante il setup del torneo, puoi selezionare velocemente i partecipanti dal database storico con lo Spazio o il doppio clic, mantenendo comunque l'editor di testo per i nuovi iscritti.
- **Case-Sensitivity per i Nickname**: Disabilitata ogni normalizzazione automatica dei caratteri per rispettare i nickname originali case-sensitive usati su DiceWorld.
- **Performance Score**: Dadillo calcola una "Media Piazzamenti" per ogni giocatore (escludendo i podi) e premia l'assiduità, rendendo la Hall of Fame molto più accurata e meritocratica anche oltre la zona medaglie.
- **Recupero Errori**: Un match inserito per sbaglio? Basta premere `Canc` nella lista dei match giocati per ripristinare i punteggi e riportarlo tra le partite aperte.

## Requisiti e Installazione

Assicurati di avere Python 3 installato e di installare la libreria `wxPython`.

```bash
pip install wxPython
```

## Avvio

Avvia l'app semplicemente eseguendo:
```bash
python Dadillo.py
```
*(Nota: All'apertura, per gli utenti screen reader, la finestra partirà ingrandita e il focus verrà sempre forzato dove serve).*

Se preferisci usare un eseguibile pre-compilato, puoi crearlo usando `pyinstaller`:
```bash
pyinstaller --name Dadillo --windowed Dadillo.py
```

## Funzionamento
- **Fase 1: Creazione**: Fornisci il nome del torneo, l'Editto, la tipologia di girone, i punteggi predefiniti e imposta i criteri di classifica e di spareggio (Vittorie/Punti, priorità punteggio alto/basso, 1° e 2° spareggio).
- **Fase 2: Le Battaglie**: La finestra principale si divide in due. A sinistra le partite da giocare, a destra quelle completate. Fai doppio clic (o premi Invio) su una partita non giocata per decretarne l'esito. Usa la barra di ricerca per filtrare velocemente le sfide di un particolare giocatore.
- **Fase 3: Classifica**: Una volta concluse tutte le partite, Dadillo elaborerà la classifica finale mostrando tempi, medaglie e record di punteggio. Da qui potrai aggiornare la "Hall of Fame" ed esportare i dati.
- **Menu dell'App**: Dal menu in alto potrai iniziare un Nuovo Torneo, Salvare, Aggiungere nuovi giocatori in corsa, Ritirare (sopprimere) un giocatore, modificare le Regole del Torneo e unire database esterni.

## Autori e Riconoscimenti

Creato e ideato da **Gabriele Battaglia**.
Hanno contribuito o fornito supporto: Bersan Vrioni, Marco De Paoli, Emanuela Pontiroli, Stella Gemini (che hanno curato la logica, la GUI e l'accessibilità).

## Licenza

Questo progetto è distribuito sotto licenza **GPL-3.0**. Vedi il file [LICENSE](LICENSE) per i dettagli.
