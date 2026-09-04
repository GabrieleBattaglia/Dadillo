"""Modelli dati, persistenza e archivio storico dei discepoli di Dadillo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import contextlib
import datetime
import json
import os
import re
import shutil
import sys
import tempfile

# Vocabolario unico dei criteri di classifica.
# Le stesse etichette vanno usate dalla creazione del torneo, dalla finestra
# delle regole e dal pannello classifica: valori diversi per la stessa cosa
# facevano perdere silenziosamente il criterio scelto.
MAIN_CRITERIA = ("Vittorie", "Punti")
RANKING_VIEWS = ("Vittorie", "Punti", "Sconfitte", "Pareggi", "Nome Giocatore")
TIEBREAKERS_1 = ("Scontro Diretto (Punti)", "Scontro Diretto (Vittorie)", "Nessuno")
TIEBREAKERS_2 = ("Punti Totali", "Vittorie Totali", "Nessuno")
DRAW_SPLITS = (
    "Inserimento Manuale",
    "Punti Pieni a Entrambi",
    "Nessun Punto",
    "Metà ciascuno",
)
SCORE_DIRECTIONS = ("Alto", "Basso")

# Come interpretare due nomi scritti nelle caselle di ricerca delle partite
SEARCH_PAIR_MODES = (
    "Coppia in qualsiasi ordine",
    "Primo nome, poi secondo",
)

# Vecchie etichette equivalenti, ancora presenti nei file salvati
MAIN_CRITERIA_ALIASES = {
    "Punti Totali": "Punti",
    "Vittorie Totali": "Vittorie",
}


def normalize_main_criterion(value):
    """Riporta il criterio principale al vocabolario ufficiale.
    Riconosce le vecchie etichette e ricade su Vittorie se il valore e' vuoto
    o non riconosciuto, cosi' un file salvato da una versione precedente non
    fa perdere l'ordinamento.
    """
    if not value:
        return MAIN_CRITERIA[0]
    testo = str(value).strip()
    testo = MAIN_CRITERIA_ALIASES.get(testo, testo)
    if testo in MAIN_CRITERIA:
        return testo
    return MAIN_CRITERIA[0]


def normalize_choice(value, valid_values, default=None):
    """Restituisce value se e' fra quelli ammessi, altrimenti il valore predefinito."""
    if value in valid_values:
        return value
    return default if default is not None else valid_values[0]


def now_local():
    """Momento attuale come datetime con il fuso orario locale."""
    return datetime.datetime.now(datetime.timezone.utc).astimezone()


def now_timestamp():
    """Momento attuale in formato ISO completo di fuso, es. 2026-09-01T14:23:45+02:00.
    Il fuso va scritto nel file: senza, la durata dei tornei veniva calcolata
    confrontando un orario locale con un orario UTC.
    """
    return now_local().replace(microsecond=0).isoformat()


def parse_timestamp(value):
    """Interpreta una data e ora salvata da Dadillo e restituisce un datetime con fuso.
    Accetta il formato ISO con fuso e il vecchio formato senza, che viene letto
    come ora locale. Restituisce None se il valore non e' interpretabile.
    """
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value if value.tzinfo else value.astimezone()
    testo = str(value).strip()
    dt = None
    with contextlib.suppress(ValueError):
        dt = datetime.datetime.fromisoformat(testo)
    if dt is None:
        # Vecchio formato senza fuso: va letto come ora locale
        with contextlib.suppress(ValueError):
            dt = datetime.datetime.strptime(testo, "%Y-%m-%d %H:%M:%S").astimezone()
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.astimezone()


def timestamp_to_fields(value):
    """Scompone una data e ora salvata nei due campi che l'utente compila.
    Restituisce ("gg/mm/aaaa", "hh:mm"), oppure due stringhe vuote se il valore
    manca o non e' interpretabile.
    """
    dt = parse_timestamp(value)
    if dt is None:
        return "", ""
    return dt.strftime("%d/%m/%Y"), dt.strftime("%H:%M")


def fields_to_timestamp(data_testo, ora_testo):
    """Compone data e ora scritte dall'utente in un timestamp con fuso locale.
    L'ora puo' mancare, e in quel caso vale mezzanotte. Solleva ValueError con
    un messaggio gia' pronto per l'utente se il formato non e' quello atteso.
    """
    data_testo = (data_testo or "").strip()
    ora_testo = (ora_testo or "").strip() or "00:00"
    if not data_testo:
        raise ValueError("la data manca")
    try:
        completo = datetime.datetime.strptime(
            f"{data_testo} {ora_testo}", "%d/%m/%Y %H:%M"
        ).astimezone()
    except ValueError:
        # Un solo parse, ma all'utente va detto quale dei due campi non va
        if not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", data_testo):
            raise ValueError(
                f"la data {data_testo} non e' nel formato giorno/mese/anno"
            ) from None
        ore_minuti = re.fullmatch(r"(\d{1,2}):(\d{2})", ora_testo)
        if not ore_minuti:
            raise ValueError(
                f"l'ora {ora_testo} non e' nel formato ore:minuti"
            ) from None
        if int(ore_minuti.group(1)) > 23 or int(ore_minuti.group(2)) > 59:
            raise ValueError(f"l'ora {ora_testo} non esiste") from None
        raise ValueError(
            f"la data {data_testo} alle {ora_testo} non esiste sul calendario"
        ) from None
    return completo.replace(microsecond=0).isoformat()


def update_history_dates(players, tourney_title, old_start, new_start, new_end):
    """Riscrive le date di un torneo nello storico di tutti i discepoli.
    Serve quando le date del torneo vengono corrette dopo la premiazione: le
    voci gia' registrate porterebbero altrimenti le date vecchie.
    Le voci si riconoscono dal titolo e dalla data di inizio precedente.
    Restituisce l'elenco dei discepoli il cui storico e' stato aggiornato.
    """
    titolo = str(tourney_title).strip()
    vecchia_inizio = format_date_extended(old_start)
    nuova_inizio = format_date_extended(new_start)
    nuova_fine = format_date_extended(new_end)
    toccati = []
    for nome, dati in players.items():
        storico = dati.get("history", [])
        cambiato = False
        for indice, voce in enumerate(storico):
            pos, voce_titolo, voce_inizio, _ = split_history_entry(voce)
            if pos is None or voce_titolo != titolo:
                continue
            if vecchia_inizio and voce_inizio != vecchia_inizio:
                continue
            storico[indice] = f"{pos}° in {titolo} - {nuova_inizio} - {nuova_fine}"
            cambiato = True
        if cambiato:
            toccati.append(nome)
    return toccati


def split_match_points(res, pts, draw_split="Metà ciascuno"):
    """Ricostruisce i punti dei due giocatori da un record partita del vecchio
    formato a quattro elementi, che non li conservava separatamente.
    Regola unica per tutto il programma: prima classifica e annullamento partita
    ne usavano due diverse e attribuivano punti differenti allo stesso record.
    """
    if res == "1":
        return pts, 0
    if res == "2":
        return 0, pts
    if draw_split == "Metà ciascuno":
        return pts / 2.0, pts / 2.0
    if draw_split == "Nessun Punto":
        return 0, 0
    # Punti Pieni a Entrambi e Inserimento Manuale
    return pts, pts


def split_history_entry(entry):
    """Scompone una voce di storico nella forma
    "3° in Torneo di Natale - data inizio - data fine".
    Restituisce posizione, titolo, data inizio e data fine. La posizione e' None
    se la voce non ha il formato atteso.
    """
    parti = str(entry).split(" - ")
    testa = parti[0]
    s_date = parti[1].strip() if len(parti) > 1 else ""
    e_date = parti[2].strip() if len(parti) > 2 else ""
    pos = None
    titolo = testa.strip()
    trovato = re.match(r"^(\d+)°\s+in\s+(.*)$", testa.strip())
    if trovato:
        pos = int(trovato.group(1))
        titolo = trovato.group(2).strip()
    return pos, titolo, s_date, e_date


# Chiavi di ordinamento per la media piazzamenti. Un giocatore che non ha mai
# chiuso fuori dal podio non ha una media da confrontare: se ha solo podi vale
# come il migliore possibile, se invece il suo storico non e' interpretabile
# finisce in fondo, perche' uno zero per mancanza di dati non e' un merito.
SOLO_PODI = float("-inf")
MEDIA_NON_DISPONIBILE = float("inf")


def placement_stats(p_data):
    """Riepilogo dei piazzamenti di un discepolo.
    Restituisce numero di tornei, media piazzamenti come chiave di ordinamento
    e testo gia' pronto da mostrare.
    """
    storico = p_data.get("history", []) or []
    tornei = len(storico)
    fuori_podio = 0
    ignote = 0
    for voce in storico:
        pos, _, _, _ = split_history_entry(voce)
        if pos is None:
            ignote += 1
        elif pos >= 5:
            fuori_podio += 1

    somma = p_data.get("placements_sum", 0)
    if fuori_podio > 0:
        # La media divide per tutti i tornei, non solo per quelli fuori dal
        # podio: e' una scelta voluta, premia l'assiduita'.
        media = somma / tornei if tornei > 0 else 0
        return tornei, media, f"{media:.2f}"
    if tornei > 0 and ignote == 0:
        return tornei, SOLO_PODI, "solo podi"
    return tornei, MEDIA_NON_DISPONIBILE, "non disponibile"


def hall_of_fame_sort_key(name, p_data):
    """Chiave di ordinamento della Hall of Fame, dal migliore al peggiore.
    Piu' medaglie prima, poi media piazzamenti piu' bassa, poi piu' tornei
    giocati, infine ordine alfabetico.
    """
    m = p_data.get("medals", {}) or {}
    tornei, media, _ = placement_stats(p_data)
    return (
        -m.get("oro", 0),
        -m.get("argento", 0),
        -m.get("bronzo", 0),
        -m.get("legno", 0),
        media,
        -tornei,
        name,
    )


def get_app_dir():
    """Cartella dell'applicazione, valida sia da sorgente sia da eseguibile PyInstaller.
    I file di dati vivono qui e non nella directory di lavoro corrente, cosi' il
    programma ritrova sempre gli stessi archivi da qualunque cartella venga avviato.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = get_app_dir()

DATA_FILENAME = "Dadillo.json"
SETTINGS_FILENAME = "Dadillo_settings.json"
PLAYERS_FILENAME = "Dadillo_players.json"
PLAYERS_TXT_FILENAME = "Giocatori.txt"

DATA_FILE = os.path.join(APP_DIR, DATA_FILENAME)
SETTINGS_FILE = os.path.join(APP_DIR, SETTINGS_FILENAME)


class SaveError(Exception):
    """Errore di scrittura di un file di dati.
    Il messaggio e' gia' pronto per essere mostrato all'utente.
    """

    def __init__(self, path, cause, message=None):
        self.path = path
        self.cause = cause
        nome = os.path.basename(path)
        super().__init__(
            message
            or (
                f"Non riesco a salvare il file {nome}.\n"
                "Puo' essere aperto in un altro\n"
                "programma, oppure il disco e' pieno\n"
                "o protetto da scrittura.\n"
                f"Dettaglio tecnico: {cause}"
            )
        )


def atomic_write_text(path, text, keep_backup=True):
    """Scrive testo su path senza mai lasciare il file a meta'.
    Il contenuto va prima in un file temporaneo nella stessa cartella, viene
    forzato su disco e solo allora sostituisce il file di destinazione con una
    operazione atomica. Della versione precedente resta una copia con estensione
    bak, cosi' un errore non cancella mai i dati gia' salvati.
    Solleva SaveError se la scrittura non riesce.
    """
    directory = os.path.dirname(path) or "."
    tmp_path = None
    try:
        os.makedirs(directory, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=directory, prefix=".dadillo_", suffix=".tmp"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if keep_backup and os.path.exists(path):
            shutil.copy2(path, path + ".bak")
        os.replace(tmp_path, path)
    except OSError as e:
        if tmp_path:
            with contextlib.suppress(OSError):
                os.remove(tmp_path)
        raise SaveError(path, e) from e


def atomic_write_json(path, data, keep_backup=True):
    """Serializza data in JSON e lo scrive con atomic_write_text."""
    try:
        text = json.dumps(data, indent=4)
    except (TypeError, ValueError) as e:
        raise SaveError(path, e) from e
    atomic_write_text(path, text, keep_backup=keep_backup)


class DataFileError(Exception):
    """Il file di dati esiste ma non e' leggibile o il contenuto non e' valido.
    Prima di sollevare questo errore il file viene messo da parte, cosi' non
    puo' essere sovrascritto da un salvataggio successivo. Il messaggio e' gia'
    pronto per essere mostrato all'utente.
    """

    def __init__(self, path, cause, quarantine_path=None):
        self.path = path
        self.cause = cause
        self.quarantine_path = quarantine_path
        nome = os.path.basename(path)
        righe = [
            f"Il file {nome} esiste ma non e'",
            "leggibile: puo' essere danneggiato",
            "o scritto da un altro programma.",
        ]
        if quarantine_path:
            righe.append("Ne ho messo da parte una copia:")
            righe.append(os.path.basename(quarantine_path))
        else:
            righe.append("Non sono riuscita a metterne")
            righe.append("da parte una copia.")
        righe.append(f"Dettaglio tecnico: {cause}")
        super().__init__("\n".join(righe))


def quarantine_file(path):
    """Mette da parte una copia del file danneggiato, con data e ora nel nome.
    L'originale non viene toccato. Restituisce il percorso della copia, oppure
    None se nemmeno la copia e' riuscita.
    """
    stamp = (
        datetime.datetime.now(datetime.timezone.utc)
        .astimezone()
        .strftime("%Y%m%d_%H%M%S")
    )
    dest = f"{path}.danneggiato_{stamp}"
    try:
        shutil.copy2(path, dest)
        return dest
    except OSError:
        return None


def _check_tournament_data(data):
    """Controlla la struttura del torneo appena letto.
    Solleva TypeError o ValueError con un messaggio comprensibile se qualcosa
    non torna.
    """
    if not isinstance(data, dict):
        raise TypeError("il contenuto non e' un insieme di dati di torneo")
    giocatori = data.get("players", {})
    if not isinstance(giocatori, dict):
        raise TypeError("l'elenco dei giocatori non ha il formato atteso")
    for name, stats in giocatori.items():
        if not isinstance(stats, list):
            raise TypeError(f"le statistiche del giocatore {name} non sono una lista")
        if len(stats) < 4:
            raise ValueError(f"le statistiche del giocatore {name} sono incomplete")
    for chiave in ("unplayed_matches", "played_matches"):
        partite = data.get(chiave, {})
        if not isinstance(partite, dict):
            raise TypeError(f"l'elenco {chiave} non ha il formato atteso")
        attesi = 2 if chiave == "unplayed_matches" else 4
        for m_id, m_data in partite.items():
            int(m_id)  # solleva ValueError se l'identificativo non e' numerico
            if not isinstance(m_data, list):
                raise TypeError(f"la partita numero {m_id} non e' una lista")
            if len(m_data) < attesi:
                raise ValueError(f"la partita numero {m_id} e' incompleta")


ITALIAN_WEEKDAYS = [
    "lunedì",
    "martedì",
    "mercoledì",
    "giovedì",
    "venerdì",
    "sabato",
    "domenica",
]

ITALIAN_MONTHS = [
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
]


def format_date_extended(date_val):
    """
    Formatta una data in formato esteso italiano, es: 'giovedì 20 agosto 2026'.
    Supporta oggetti datetime/date, stringhe ISO ('2026-08-20', '2026-08-20 15:30:00')
    e stringhe già parzialmente o totalmente formattate.
    """
    if not date_val:
        return ""

    if isinstance(date_val, (datetime.date, datetime.datetime)):
        w = ITALIAN_WEEKDAYS[date_val.weekday()]
        m = ITALIAN_MONTHS[date_val.month - 1]
        return f"{w} {date_val.day} {m} {date_val.year}"

    if isinstance(date_val, str):
        val = date_val.strip()
        if not val:
            return ""

        # Controllo se è già una data estesa (inizia con giorno della settimana)
        for w in ITALIAN_WEEKDAYS:
            if val.lower().startswith(w):
                return val

        # Prova parsing formato ISO standard: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS
        iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", val)
        if iso_match:
            with contextlib.suppress(ValueError, TypeError, IndexError, AttributeError):
                y = int(iso_match.group(1))
                m = int(iso_match.group(2))
                d = int(iso_match.group(3))
                dt = datetime.date(y, m, d)
                w = ITALIAN_WEEKDAYS[dt.weekday()]
                m_str = ITALIAN_MONTHS[dt.month - 1]
                return f"{w} {d} {m_str} {y}"

        # Prova parsing formato '1 agosto 2026' o '01 agosto 2026'
        ita_match = re.match(r"^(\d{1,2})\s+([a-zA-Zàèéìòù]+)\s+(\d{4})", val)
        if ita_match:
            with contextlib.suppress(ValueError, TypeError, IndexError, AttributeError):
                d = int(ita_match.group(1))
                m_name = ita_match.group(2).lower()
                y = int(ita_match.group(3))
                if m_name in ITALIAN_MONTHS:
                    m_idx = ITALIAN_MONTHS.index(m_name) + 1
                    dt = datetime.date(y, m_idx, d)
                    w = ITALIAN_WEEKDAYS[dt.weekday()]
                    return f"{w} {d} {m_name} {y}"

        return val

    return str(date_val)


class TournamentData:
    def __init__(self, base_dir=None):
        # base_dir serve ai test per lavorare su una cartella temporanea.
        # Nell'uso normale i dati stanno sempre accanto all'applicazione.
        self.base_dir = base_dir or APP_DIR
        self.filename = os.path.join(self.base_dir, DATA_FILENAME)
        self.title = ""
        self.comment = ""
        self.start_date = ""
        self.end_date = ""
        self.players = {}  # name -> [points, wins, draws, losses]
        self.unplayed_matches = {}  # id -> [p1, p2]
        self.played_matches = {}  # id -> [p1, p2, result, points]
        # result: 1=p1, 2=p2, 3=draw
        # I record del torneo non sono piu' campi salvati: la schermata della
        # classifica li ricalcola sempre dalle partite giocate.

        # v2.1.0 new fields
        self.tourney_type = 0  # 0 = Andata e Ritorno, 1 = Solo Andata
        self.pts_win = None
        self.pts_draw = None
        self.pts_loss = None

        # v2.6.0 ranking & tiebreak criteria fields
        self.main_criterion = "Vittorie"  # Vittorie o Punti
        self.score_direction = (
            "Alto"  # Alto (più alto è migliore) o Basso (più basso è migliore)
        )
        self.tiebreaker_1 = "Scontro Diretto (Punti)"
        self.tiebreaker_2 = "Punti Totali"
        self.draw_points_split = "Inserimento Manuale"

    def save(self):
        data = {
            "title": self.title,
            "comment": self.comment,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "players": self.players,
            "unplayed_matches": self.unplayed_matches,
            "played_matches": self.played_matches,
            "tourney_type": self.tourney_type,
            "pts_win": self.pts_win,
            "pts_draw": self.pts_draw,
            "pts_loss": self.pts_loss,
            "main_criterion": self.main_criterion,
            "score_direction": self.score_direction,
            "tiebreaker_1": self.tiebreaker_1,
            "tiebreaker_2": self.tiebreaker_2,
            "draw_points_split": self.draw_points_split,
        }
        atomic_write_json(self.filename, data)

    def _migrate_played_matches(self):
        """Porta le partite del vecchio formato a quattro elementi a quello
        completo [p1, p2, esito, punti, punti1, punti2].
        La conversione avviene una volta sola al caricamento, con la regola dei
        pareggi del torneo: prima ogni parte del programma la ricostruiva al
        volo, e non tutte allo stesso modo.
        """
        for m_id, record in self.played_matches.items():
            if len(record) >= 6:
                continue
            p1, p2, res, pts = record[:4]
            pt1, pt2 = split_match_points(res, pts, self.draw_points_split)
            self.played_matches[m_id] = [p1, p2, res, pts, pt1, pt2]

    def load(self):
        """Carica il torneo.
        Restituisce True se il torneo e' stato caricato e False se il file non
        esiste. Se il file esiste ma non e' leggibile o valido solleva
        DataFileError, dopo averne messo da parte una copia: cosi' un archivio
        danneggiato non viene mai scambiato per assenza di torneo e sovrascritto.
        """
        if not os.path.exists(self.filename):
            return False
        try:
            with open(self.filename, encoding="utf-8") as f:
                data = json.load(f)
            _check_tournament_data(data)
        except (json.JSONDecodeError, OSError, ValueError, TypeError) as e:
            raise DataFileError(self.filename, e, quarantine_file(self.filename)) from e
        try:
            self.title = data.get("title", "")
            self.comment = data.get("comment", "")
            self.start_date = data.get("start_date", "")
            self.end_date = data.get("end_date", "")
            self.players = data.get("players", {})
            self.unplayed_matches = {
                int(k): v for k, v in data.get("unplayed_matches", {}).items()
            }
            self.played_matches = {
                int(k): v for k, v in data.get("played_matches", {}).items()
            }
            self.tourney_type = data.get("tourney_type", 0)
            self.pts_win = data.get("pts_win", None)
            self.pts_draw = data.get("pts_draw", None)
            self.pts_loss = data.get("pts_loss", None)
            # Normalizzazione: i file salvati da versioni precedenti possono
            # contenere etichette diverse per lo stesso criterio, o valori vuoti.
            self.main_criterion = normalize_main_criterion(data.get("main_criterion"))
            self.score_direction = normalize_choice(
                data.get("score_direction"), SCORE_DIRECTIONS
            )
            self.tiebreaker_1 = normalize_choice(
                data.get("tiebreaker_1"), TIEBREAKERS_1
            )
            self.tiebreaker_2 = normalize_choice(
                data.get("tiebreaker_2"), TIEBREAKERS_2
            )
            self.draw_points_split = normalize_choice(
                data.get("draw_points_split"), DRAW_SPLITS
            )
            self._migrate_played_matches()
            return True
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            raise DataFileError(self.filename, e, quarantine_file(self.filename)) from e


class SettingsData:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or APP_DIR
        self.filename = os.path.join(self.base_dir, SETTINGS_FILENAME)
        self.main_criterion = "Vittorie"  # Vittorie o Punti
        self.score_direction = (
            "Alto"  # Alto (più alto è migliore) o Basso (più basso è migliore)
        )
        self.tiebreaker_1 = "Scontro Diretto (Punti)"  # Scontro Diretto (Punti) o Scontro Diretto (Vittorie)
        self.tiebreaker_2 = "Punti Totali"  # Punti Totali o Vittorie Totali
        self.draw_points_split = "Inserimento Manuale"  # "Inserimento Manuale", "Punti Pieni a Entrambi", "Nessun Punto", "Metà ciascuno"
        self.search_pair_mode = SEARCH_PAIR_MODES[0]

    def save(self):
        data = {
            "main_criterion": self.main_criterion,
            "score_direction": self.score_direction,
            "tiebreaker_1": self.tiebreaker_1,
            "tiebreaker_2": self.tiebreaker_2,
            "draw_points_split": self.draw_points_split,
            "search_pair_mode": self.search_pair_mode,
        }
        atomic_write_json(self.filename, data)

    def load(self):
        if not os.path.exists(self.filename):
            # Primo avvio: se le impostazioni non si riescono a scrivere il
            # programma parte comunque con i valori predefiniti.
            with contextlib.suppress(SaveError):
                self.save()
            return True
        try:
            with open(self.filename, encoding="utf-8") as f:
                data = json.load(f)
            self.main_criterion = normalize_main_criterion(data.get("main_criterion"))
            self.score_direction = normalize_choice(
                data.get("score_direction"), SCORE_DIRECTIONS
            )
            self.tiebreaker_1 = normalize_choice(
                data.get("tiebreaker_1"), TIEBREAKERS_1
            )
            self.tiebreaker_2 = normalize_choice(
                data.get("tiebreaker_2"), TIEBREAKERS_2
            )
            self.draw_points_split = normalize_choice(
                data.get("draw_points_split"), DRAW_SPLITS
            )
            self.search_pair_mode = normalize_choice(
                data.get("search_pair_mode"), SEARCH_PAIR_MODES
            )
            return True
        except (json.JSONDecodeError, OSError, ValueError, KeyError, AttributeError):
            return False


class PlayerDB:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or APP_DIR
        self.filename = os.path.join(self.base_dir, PLAYERS_FILENAME)
        self.txt_filename = os.path.join(self.base_dir, PLAYERS_TXT_FILENAME)
        self.players = {}  # name -> {"medals": {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0}, "history": [], "placements_sum": 0}
        self.load_error = None
        self.load()

    def load(self):
        """Carica l'archivio dei giocatori.
        Se il file esiste ma non e' leggibile, l'archivio resta vuoto, ne viene
        messa da parte una copia e l'errore viene ricordato in self.load_error.
        Finche' quell'errore e' presente ogni salvataggio viene rifiutato, cosi'
        la Hall of Fame non puo' essere sovrascritta da un archivio vuoto.
        """
        self.load_error = None
        if os.path.exists(self.filename):
            try:
                with open(self.filename, encoding="utf-8") as f:
                    caricati = json.load(f)
                if not isinstance(caricati, dict):
                    raise TypeError("il contenuto non e' un elenco di giocatori")
                for nome, p in caricati.items():
                    if not isinstance(p, dict):
                        raise TypeError(
                            f"i dati del giocatore {nome} non hanno il formato atteso"
                        )
                self.players = caricati
            except (json.JSONDecodeError, OSError, ValueError, TypeError) as e:
                self.players = {}
                self.load_error = DataFileError(
                    self.filename, e, quarantine_file(self.filename)
                )
                return False

        # Migrazione DB: aggiunge placements_sum e normalizza date in formato esteso
        for data in self.players.values():
            if "history" in data:
                new_hist = []
                for entry in data["history"]:
                    parts = entry.split(" - ")
                    if len(parts) == 3:
                        pos_title, s_date, e_date = parts
                        new_hist.append(
                            f"{pos_title} - {format_date_extended(s_date)} - {format_date_extended(e_date)}"
                        )
                    else:
                        new_hist.append(entry)
                data["history"] = new_hist

            if "placements_sum" not in data:
                data["placements_sum"] = 0
                for entry in data.get("history", []):
                    pos, _, _, _ = split_history_entry(entry)
                    if pos is not None and pos >= 5:
                        data["placements_sum"] += pos
        return True

    def save(self):
        if self.load_error:
            raise SaveError(
                self.filename,
                self.load_error.cause,
                message=(
                    "Non salvo l'archivio dei discepoli.\n"
                    "All'avvio non era leggibile e in\n"
                    "memoria e' vuoto: salvarlo ora\n"
                    "cancellerebbe la Hall of Fame.\n"
                    "Ripristina prima il file, partendo\n"
                    "dalla copia messa da parte."
                ),
            )
        atomic_write_json(self.filename, self.players)
        self.export_to_txt()

    def recalculate_player_stats(self, name):
        """Ricalcola in modo deterministico medaglie e somma piazzamenti a partire dallo storico effettivo."""
        if name not in self.players:
            return
        p = self.players[name]
        p["medals"] = {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0}
        p["placements_sum"] = 0

        medaglia_per_posizione = {1: "oro", 2: "argento", 3: "bronzo", 4: "legno"}
        for entry in p.get("history", []):
            pos, _, _, _ = split_history_entry(entry)
            if pos is None:
                continue
            if pos in medaglia_per_posizione:
                p["medals"][medaglia_per_posizione[pos]] += 1
            elif pos >= 5:
                p["placements_sum"] += pos

    def add_or_update_player(
        self,
        name,
        position,
        tourney_title,
        start_date,
        end_date,
    ):
        """Registra il piazzamento di un discepolo in un torneo.
        Le medaglie non sono parametri: si ricavano dalla posizione, che e'
        l'unica fonte di verita', con recalculate_player_stats.
        """
        actual_name = name

        if actual_name not in self.players:
            self.players[actual_name] = {
                "medals": {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0},
                "history": [],
                "placements_sum": 0,
            }

        p = self.players[actual_name]

        s_fmt = format_date_extended(start_date)
        e_fmt = format_date_extended(end_date)
        # Es: 3° in Torneo di Natale - giovedì 25 dicembre 2026 - venerdì 15 gennaio 2027
        history_entry = f"{position}° in {tourney_title} - {s_fmt} - {e_fmt}"

        # Controllo duplicati: titolo e data di inizio si confrontano per intero,
        # non come sottostringhe. Con il vecchio confronto un titolo breve o
        # ricorrente faceva scartare per errore un torneo nuovo.
        s_originale = str(start_date).strip()
        for existing_entry in p["history"]:
            _, titolo_esistente, s_esistente, _ = split_history_entry(existing_entry)
            if titolo_esistente == str(tourney_title).strip() and s_esistente in (
                s_fmt,
                s_originale,
            ):
                return False  # Già aggiunto in precedenza

        p["history"].append(history_entry)
        self.recalculate_player_stats(actual_name)
        return True

    def merge_db(self, external_filepath, interactive_resolver=None):
        log = []
        try:
            with open(external_filepath, encoding="utf-8") as f:
                ext_data = json.load(f)
        except (json.JSONDecodeError, OSError, ValueError, KeyError) as e:
            return False, [f"Errore nella lettura del file: {e}"]

        if not isinstance(ext_data, dict):
            return False, ["Il file non e' nel formato corretto."]

        import difflib

        for ext_name, ext_p in ext_data.items():
            if not isinstance(ext_p, dict) or "history" not in ext_p:
                continue

            target_name = ext_name

            if target_name not in self.players:
                # Ricerca candidati simili nel DB locale con difflib
                candidates = []
                for local_name in list(self.players.keys()):
                    ratio = difflib.SequenceMatcher(
                        None, ext_name.lower(), local_name.lower()
                    ).ratio()
                    if (
                        ext_name.lower() in local_name.lower()
                        or local_name.lower() in ext_name.lower()
                        or ratio >= 0.6
                    ):
                        candidates.append((local_name, ratio))

                candidates.sort(key=lambda x: x[1], reverse=True)

                if candidates and interactive_resolver:
                    best_candidate = candidates[0][0]
                    is_same, chosen_name = interactive_resolver(
                        ext_name, best_candidate
                    )
                    if is_same and chosen_name:
                        if (
                            chosen_name != best_candidate
                            and best_candidate in self.players
                        ):
                            if chosen_name in self.players:
                                # Il nome scelto appartiene gia' a un altro discepolo:
                                # i due storici vengono fusi, mai sovrascritti.
                                dati_da_unire = self.players.pop(best_candidate)
                                storico = self.players[chosen_name].setdefault(
                                    "history", []
                                )
                                aggiunte = 0
                                for voce in dati_da_unire.get("history", []):
                                    if voce not in storico:
                                        storico.append(voce)
                                        aggiunte += 1
                                self.recalculate_player_stats(chosen_name)
                                log.append(
                                    f"'{best_candidate}' e '{chosen_name}' erano gia' entrambi in archivio: storici uniti sotto '{chosen_name}', {aggiunte} tornei aggiunti."
                                )
                            else:
                                self.players[chosen_name] = self.players.pop(
                                    best_candidate
                                )
                                log.append(
                                    f"Discepolo '{best_candidate}' rinominato in '{chosen_name}' per unione."
                                )
                        target_name = chosen_name

            if target_name not in self.players:
                self.players[target_name] = {
                    "medals": {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0},
                    "history": [],
                    "placements_sum": 0,
                }
                log.append(f"Nuovo discepolo immolato negli archivi: {target_name}")

            # Fusione intelligente e atomica dello storico tornei (senza duplicare medaglie)
            ext_history = ext_p.get("history", [])
            for entry in ext_history:
                parts = entry.split(" - ")
                if len(parts) == 3:
                    pos_title, s_date, e_date = parts
                    formatted_entry = f"{pos_title} - {format_date_extended(s_date)} - {format_date_extended(e_date)}"
                else:
                    formatted_entry = entry

                # Due voci descrivono lo stesso torneo se coincidono titolo e date
                _, titolo_ext, s_ext, e_ext = split_history_entry(formatted_entry)
                already_present = False
                for local_entry in self.players[target_name]["history"]:
                    if formatted_entry == local_entry or entry == local_entry:
                        already_present = True
                        break
                    _, titolo_loc, s_loc, e_loc = split_history_entry(local_entry)
                    if (titolo_ext, s_ext, e_ext) == (titolo_loc, s_loc, e_loc):
                        already_present = True
                        break

                if not already_present:
                    self.players[target_name]["history"].append(formatted_entry)
                    log.append(f"  Aggiunto torneo a {target_name}: {formatted_entry}")

            # Ricalcolo rigoroso dei contatori medaglie dal nuovo storico
            self.recalculate_player_stats(target_name)

        self.save()
        if not log:
            log.append(
                "Nessuna novità trovata nel file importato. I discepoli e i tornei erano già allineati."
            )
        else:
            log.append("Fusione sacra completata e archivi aggiornati con successo!")
        return True, log

    def export_to_txt(self):
        if self.load_error:
            raise SaveError(
                self.txt_filename,
                self.load_error.cause,
                message=(
                    "Non esporto la Hall of Fame.\n"
                    "L'archivio dei discepoli non era\n"
                    "leggibile all'avvio e in memoria\n"
                    "e' vuoto: il file di testo\n"
                    "risulterebbe cancellato.\n"
                    "Ripristina prima l'archivio."
                ),
            )
        parts = ["Hall of Fame di Dadillo\n"]

        # Ordinamento: prima chi ha piu' ori, poi argenti, bronzi e legni; a pari
        # medagliere vince la media piazzamenti piu' bassa, poi chi ha giocato
        # piu' tornei, infine l'ordine alfabetico. Una sola chiave a tupla al
        # posto della funzione di confronto scritta a mano.
        sorted_players = sorted(
            self.players.items(), key=lambda item: hall_of_fame_sort_key(*item)
        )

        for name, p in sorted_players:
            m = p["medals"]

            # Livello 0: Nome
            parts.append(f"{name}\n")

            # Livello 1: Medagliere e Intestazione Storico
            medals_str_parts = []
            if m["oro"] >= 1:
                medals_str_parts.append(f"Oro {m['oro']}")
            if m["argento"] >= 1:
                medals_str_parts.append(f"Argento {m['argento']}")
            if m["bronzo"] >= 1:
                medals_str_parts.append(f"Bronzo {m['bronzo']}")
            if m["legno"] >= 1:
                medals_str_parts.append(f"Legno {m['legno']}")

            if medals_str_parts:
                medals_line = "  Medagliere: " + ", ".join(medals_str_parts) + "\n"
            else:
                medals_line = "  Medagliere: Ancora nessuna medaglia\n"
            parts.append(medals_line)

            num_tornei, _, media_testo = placement_stats(p)
            parts.append(
                f"  Media piazzamenti {media_testo}, tornei giocati {num_tornei}.\n"
            )

            parts.append("  Storico Tornei:\n")

            # Livello 2: Tornei
            parts.extend(f"    {h}\n" for h in p["history"])

        # Niente copia di sicurezza: Giocatori.txt e' un file derivato, che si
        # rigenera dall'archivio a ogni variazione dello storico e su richiesta
        # con Esporta Hall of Fame.
        atomic_write_text(self.txt_filename, "".join(parts), keep_backup=False)
