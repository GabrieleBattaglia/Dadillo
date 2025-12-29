# Dadillo - DiceWorld Tournament Manager

**Dadillo** è un gestore di tornei per DiceWorld scritto in Python. Gestisce giocatori, abbinamenti, classifiche e record con una personalità... *molto devota* al suo utilizzatore.

## Descrizione

Questo strumento permette di gestire interi tornei, calcolando automaticamente:
- Abbinamenti (Round Robin/Girone all'italiana).
- Classifiche basate su Criterio utente > Scontro Diretto > Punti Totali > Ordine Alfabetico.
- Record di punteggio (massimo e minimo).
- Salvataggio e ripristino dello stato del torneo tramite database JSON.

## Installazione e Avvio

Assicurati di avere Python 3 installato.

```bash
python Dadillo.py
```

Al primo avvio, il programma ti guiderà nella creazione di un nuovo torneo, chiedendoti di inserire i nomi dei partecipanti.

## Comandi del Menù

Dal menu principale (accessibile digitando `m`), sono disponibili i seguenti comandi:

*   **AGT** (Aggiungi Giocatore al Torneo): Inserisce un nuovo partecipante a torneo in corso, rigenerando gli abbinamenti necessari.
*   **CLA** (Classifica): Mostra la classifica attuale. È possibile ordinare per Punti, Vittorie, Pareggi, Sconfitte e scegliere l'ordine ascendente o discendente.
*   **CLAAV** (Classifica Avulsa): Calcola la classifica parziale per gruppi di 3 o più giocatori a pari vittorie.
*   **LG** (Lista Giocatori): Elenco semplice dei partecipanti e dei loro punteggi attuali.
*   **LPC** (Lista Partite Completate): Storico dei match conclusi.
*   **LPI** (Lista Partite Incomplete): Elenco dei match ancora da giocare.
*   **MSG** (Modifica Situazione Giocatore): Permette di correggere manualmente i punteggi di un giocatore o di rimuoverlo dal torneo (le sue partite verranno spostate nello storico).
*   **OK** (Partita completata!): Registra il risultato di un match. Richiede il numero della partita (visibile in LPI).
*   **SPI** (Sposta Partita nelle Incomplete): Utile se si è marcata una partita come completata per errore; la riporta tra quelle da giocare.
*   **CAN** (Annulla l'ultima partita): Annulla l'ultima operazione di inserimento risultato.
*   **SAV** (Salva manualmente): Forza il salvataggio dei dati su disco.
*   **U** (Uscita): Chiude il programma.

## Autori e Riconoscimenti

Creato da **Gabriele Battaglia**.
Hanno contribuito o fornito supporto: Bersan Vrioni, Marco De Paoli, Emanuela Pontiroli, ChatGPT e Gemini.

## Licenza

Questo progetto è distribuito sotto licenza **GPL-3.0**. Vedi il file [LICENSE](LICENSE) per i dettagli.
