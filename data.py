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
        self.records_high = ["Giocatore sconosciuto", "Partita sconosciuta", -99999]
        self.records_low = ["Giocatore sconosciuto", "Partita sconosciuta", 99999]

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
            "records_high": self.records_high,
            "records_low": self.records_low,
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
            with open(self.filename, "r", encoding="utf-8") as f:
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
            self.records_high = data.get("records_high", ["", "", -99999])
            self.records_low = data.get("records_low", ["", "", 99999])
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

    def save(self):
        data = {
            "main_criterion": self.main_criterion,
            "score_direction": self.score_direction,
            "tiebreaker_1": self.tiebreaker_1,
            "tiebreaker_2": self.tiebreaker_2,
            "draw_points_split": self.draw_points_split,
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
            with open(self.filename, "r", encoding="utf-8") as f:
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
                with open(self.filename, "r", encoding="utf-8") as f:
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
        import re

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
                    match = re.match(r"^(\d+)°", entry)
                    if match:
                        pos = int(match.group(1))
                        if pos >= 5:
                            data["placements_sum"] += pos

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

        import re

        for entry in p.get("history", []):
            match = re.match(r"^(\d+)°", entry)
            if match:
                pos = int(match.group(1))
                if pos == 1:
                    p["medals"]["oro"] += 1
                elif pos == 2:
                    p["medals"]["argento"] += 1
                elif pos == 3:
                    p["medals"]["bronzo"] += 1
                elif pos == 4:
                    p["medals"]["legno"] += 1
                elif pos >= 5:
                    p["placements_sum"] += pos

    def add_or_update_player(
        self,
        name,
        position,
        is_oro,
        is_argento,
        is_bronzo,
        is_legno,
        tourney_title,
        start_date,
        end_date,
    ):
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

        # Controllo duplicati: se il torneo è già presente nella storia, non aggiungerlo.
        for existing_entry in p["history"]:
            if existing_entry == history_entry or (
                tourney_title in existing_entry
                and (start_date in existing_entry or s_fmt in existing_entry)
            ):
                return False  # Già aggiunto in precedenza

        p["history"].append(history_entry)
        self.recalculate_player_stats(actual_name)
        return True

    def merge_db(self, external_filepath, interactive_resolver=None):
        log = []
        try:
            with open(external_filepath, "r", encoding="utf-8") as f:
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

                already_present = False
                for local_entry in self.players[target_name]["history"]:
                    if formatted_entry == local_entry or entry == local_entry:
                        already_present = True
                        break
                    if " in " in formatted_entry and " in " in local_entry:
                        t_part_ext = formatted_entry.split(" in ", 1)[1]
                        t_part_loc = local_entry.split(" in ", 1)[1]
                        if t_part_ext == t_part_loc:
                            already_present = True
                            break

                if not already_present:
                    self.players[target_name]["history"].append(formatted_entry)
                    log.append(
                        f"  + Aggiunto torneo a {target_name}: {formatted_entry}"
                    )

            # Ricalcolo rigoroso dei contatori medaglie dal nuovo storico
            self.recalculate_player_stats(target_name)

        self.save()
        if not log:
            log.append(
                "Nessuna novità trovata nel file importato. I discepoli e i tornei erano già allineati."
            )
        else:
            log.append("\nFusione sacra completata e archivi aggiornati con successo!")
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
        parts = ["Hall of Fame di Dadillo\n\n"]

        # Funzione per ordinamento: prima ori, poi argenti, poi bronzi, poi legni (tutti in ordine decrescente = chi ne ha di più sta in cima)
        # Poi ordina per media piazzamenti (somma piazzamenti >= 5 / numero tornei) decrescente (la media più bassa sta in cima)
        # e infine ordina per quantità di tornei giocati (per risolvere i parimerito) e per nome alfabetico.
        import functools

        def compare_db_players(a_item, b_item):
            name_a, data_a = a_item
            name_b, data_b = b_item

            m_a = data_a["medals"]
            m_b = data_b["medals"]

            if m_a["oro"] != m_b["oro"]:
                return (m_b["oro"] > m_a["oro"]) - (m_b["oro"] < m_a["oro"])
            if m_a["argento"] != m_b["argento"]:
                return (m_b["argento"] > m_a["argento"]) - (
                    m_b["argento"] < m_a["argento"]
                )
            if m_a["bronzo"] != m_b["bronzo"]:
                return (m_b["bronzo"] > m_a["bronzo"]) - (m_b["bronzo"] < m_a["bronzo"])
            if m_a["legno"] != m_b["legno"]:
                return (m_b["legno"] > m_a["legno"]) - (m_b["legno"] < m_a["legno"])

            # Calcolo media piazzamenti
            len_a = len(data_a["history"])
            len_b = len(data_b["history"])
            avg_a = data_a.get("placements_sum", 0) / len_a if len_a > 0 else 0
            avg_b = data_b.get("placements_sum", 0) / len_b if len_b > 0 else 0

            if avg_a != avg_b:
                return (avg_a > avg_b) - (avg_a < avg_b)

            # Spareggio ulteriore: numero di partecipazioni
            if len_a != len_b:
                return (len_b > len_a) - (len_b < len_a)

            # Alfabetico
            return (name_a > name_b) - (name_a < name_b)

        sorted_players = sorted(
            self.players.items(), key=functools.cmp_to_key(compare_db_players)
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

            num_tornei = len(p["history"])
            media = p.get("placements_sum", 0) / num_tornei if num_tornei > 0 else 0
            parts.append(
                f"  Media Piazzamenti: {media:.2f} (Tornei giocati: {num_tornei})\n"
            )

            parts.append("  Storico Tornei:\n")

            # Livello 2: Tornei
            parts.extend(f"    {h}\n" for h in p["history"])

            parts.append("\n")

        atomic_write_text(self.txt_filename, "".join(parts))
