# Dadillo - L'Altare del Sacrificio (Versione 2.1.2)

**Dadillo** è un gestore di tornei scritto in Python. Gestisce giocatori, abbinamenti, classifiche e record con una personalità... *molto devota* al suo utilizzatore.
La versione 2.1.2 introduce un'interfaccia grafica (GUI) completamente accessibile sviluppata in `wxPython`.

## Caratteristiche
- **Interfaccia Grafica**: Liste interattive, finestre di dialogo chiare e complete di supporto screen reader (NVDA/Jaws).
- **Gestione Tornei Round Robin**: Calcola automaticamente gli abbinamenti di andata e ritorno.
- **Classifiche Avanzate**: Ordinamento configurabile per Vittorie o Punti. Gestione intelligente degli spareggi tramite Scontri Diretti (Punti o Vittorie) integrando la Classifica Avulsa.
- **Opzioni Personalizzabili**: Decidi tu come spartire i punti in caso di pareggio (Manuale, Metà ciascuno, Nessun punto, ecc.).
- **Hall of Fame**: Un database storico testuale (`Giocatori.txt`) e strutturato (`Dadillo_players.json`) che tiene traccia per sempre del medagliere globale (Ori, Argenti, Bronzi e Legni) e di tutte le partecipazioni dei tuoi discepoli.
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
- **Fase 1: Creazione**: Fornisci il nome del torneo, un commento (Editto) e inserisci i nomi dei giocatori (minimo 3 caratteri).
- **Fase 2: Le Battaglie**: La finestra principale si divide in due. A sinistra le partite da giocare, a destra quelle completate. Fai doppio clic (o premi Invio) su una partita non giocata per decretarne l'esito. Usa la barra di ricerca per filtrare velocemente le sfide di un particolare giocatore.
- **Fase 3: Classifica**: Una volta concluse tutte le partite, Dadillo elaborerà la classifica finale mostrando tempi, medaglie e record di punteggio. Da qui potrai esportare i dati nel "Hall of Fame".
- **Menu dell'App**: Dal menu in alto potrai iniziare un Nuovo Torneo, Salvare, Aggiungere nuovi giocatori in corsa, Ritirare (sopprimere) un giocatore e modificare le Regole del Torneo.

## Autori e Riconoscimenti

Creato e ideato da **Gabriele Battaglia**.
Hanno contribuito o fornito supporto: Bersan Vrioni, Marco De Paoli, Emanuela Pontiroli, ChatGPT e Gemini (che hanno curato il refactoring e la GUI).

## Licenza

Questo progetto è distribuito sotto licenza **GPL-3.0**. Vedi il file [LICENSE](LICENSE) per i dettagli.
