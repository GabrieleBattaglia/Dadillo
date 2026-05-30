import json
import os

DATA_FILE = "Dadillo.json"
SETTINGS_FILE = "Dadillo_settings.json"

class TournamentData:
    def __init__(self):
        self.title = ""
        self.comment = ""
        self.start_date = ""
        self.end_date = ""
        self.players = {} # name -> [points, wins, draws, losses]
        self.unplayed_matches = {} # id -> [p1, p2]
        self.played_matches = {} # id -> [p1, p2, result, points]
        # result: 1=p1, 2=p2, 3=draw
        self.records_high = ["Giocatore sconosciuto", "Partita sconosciuta", -99999]
        self.records_low = ["Giocatore sconosciuto", "Partita sconosciuta", 99999]
        
        # v2.1.0 new fields
        self.tourney_type = 0 # 0 = Andata e Ritorno, 1 = Solo Andata
        self.pts_win = None
        self.pts_draw = None
        self.pts_loss = None
        
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
            "pts_loss": self.pts_loss
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
    def load(self):
        if not os.path.exists(DATA_FILE):
            return False
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.title = data.get("title", "")
            self.comment = data.get("comment", "")
            self.start_date = data.get("start_date", "")
            self.end_date = data.get("end_date", "")
            self.players = data.get("players", {})
            self.unplayed_matches = {int(k): v for k, v in data.get("unplayed_matches", {}).items()}
            self.played_matches = {int(k): v for k, v in data.get("played_matches", {}).items()}
            self.records_high = data.get("records_high", ["", "", -99999])
            self.records_low = data.get("records_low", ["", "", 99999])
            self.tourney_type = data.get("tourney_type", 0)
            self.pts_win = data.get("pts_win", None)
            self.pts_draw = data.get("pts_draw", None)
            self.pts_loss = data.get("pts_loss", None)
            return True
        except Exception:
            return False


class SettingsData:
    def __init__(self):
        self.main_criterion = "Vittorie" # Vittorie o Punti
        self.tiebreaker_1 = "Scontro Diretto (Punti)" # Scontro Diretto (Punti) o Scontro Diretto (Vittorie)
        self.tiebreaker_2 = "Punti Totali" # Punti Totali o Vittorie Totali
        self.draw_points_split = "Inserimento Manuale" # "Inserimento Manuale", "Punti Pieni a Entrambi", "Nessun Punto", "Metà ciascuno"
        
    def save(self):
        data = {
            "main_criterion": self.main_criterion,
            "tiebreaker_1": self.tiebreaker_1,
            "tiebreaker_2": self.tiebreaker_2,
            "draw_points_split": self.draw_points_split
        }
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
    def load(self):
        if not os.path.exists(SETTINGS_FILE):
            self.save()
            return True
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.main_criterion = data.get("main_criterion", "Vittorie")
            self.tiebreaker_1 = data.get("tiebreaker_1", "Scontro Diretto (Punti)")
            self.tiebreaker_2 = data.get("tiebreaker_2", "Punti Totali")
            self.draw_points_split = data.get("draw_points_split", "Inserimento Manuale")
            return True
        except Exception:
            return False

class PlayerDB:
    def __init__(self):
        self.filename = "Dadillo_players.json"
        self.txt_filename = "Giocatori.txt"
        self.players = {} # name -> {"medals": {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0}, "history": [], "placements_sum": 0}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.players = json.load(f)
            except Exception:
                self.players = {}
                
        # Migrazione DB: aggiunge placements_sum ai giocatori esistenti se manca
        import re
        for name, data in self.players.items():
            if "placements_sum" not in data:
                data["placements_sum"] = 0
                for entry in data.get("history", []):
                    match = re.match(r"^(\d+)°", entry)
                    if match:
                        pos = int(match.group(1))
                        if pos >= 5:
                            data["placements_sum"] += pos

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.players, f, indent=4)
        self.export_to_txt()

    def add_or_update_player(self, name, position, is_oro, is_argento, is_bronzo, is_legno, tourney_title, start_date, end_date):
        actual_name = name

        if actual_name not in self.players:
            self.players[actual_name] = {"medals": {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0}, "history": [], "placements_sum": 0}

        p = self.players[actual_name]
        
        # Es: 3° in Torneo di Natale - 25 dicembre 2026 - 15 gennaio 2027
        history_entry = f"{position}° in {tourney_title} - {start_date} - {end_date}"
        
        # Controllo duplicati: se il torneo è già presente nella storia, non aggiungerlo.
        for existing_entry in p["history"]:
            if tourney_title in existing_entry and start_date in existing_entry:
                return False # Già aggiunto in precedenza
                
        if is_oro:
            p["medals"]["oro"] += 1
        if is_argento:
            p["medals"]["argento"] += 1
        if is_bronzo:
            p["medals"]["bronzo"] += 1
        if is_legno:
            p["medals"]["legno"] += 1

        if position >= 5:
            if "placements_sum" not in p:
                p["placements_sum"] = 0
            p["placements_sum"] += position

        p["history"].append(history_entry)
        return True
        
    def merge_db(self, external_filepath):
        log = []
        try:
            with open(external_filepath, 'r', encoding='utf-8') as f:
                ext_data = json.load(f)
        except Exception as e:
            return False, [f"Errore nella lettura del file: {e}"]

        if not isinstance(ext_data, dict):
            return False, ["Il file non e' nel formato corretto."]

        import re
        for ext_name, ext_p in ext_data.items():
            if not isinstance(ext_p, dict) or "medals" not in ext_p or "history" not in ext_p:
                continue

            # Check for existing player (case insensitive)
            actual_name = ext_name

            if actual_name not in self.players:
                self.players[actual_name] = {"medals": {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0}, "history": [], "placements_sum": 0}
                log.append(f"Nuovo giocatore aggiunto: {actual_name}")

            p = self.players[actual_name]

            # Merge medals
            for medal_type in ["oro", "argento", "bronzo", "legno"]:
                added = ext_p["medals"].get(medal_type, 0)
                if added > 0:
                    p["medals"][medal_type] += added
                    log.append(f"  + Aggiunte {added} medaglie {medal_type.capitalize()} a {actual_name}")

            # Merge history
            ext_history = ext_p.get("history", [])
            for entry in ext_history:
                # Check for duplicates based on exact string match
                if entry not in p["history"]:
                    p["history"].append(entry)
                    log.append(f"  + Aggiunto torneo a {actual_name}: {entry}")
                    
                    # Update placements_sum
                    match = re.match(r"^(\d+)°", entry)
                    if match:
                        pos = int(match.group(1))
                        if pos >= 5:
                            p["placements_sum"] = p.get("placements_sum", 0) + pos

        self.save()
        if not log:
            log.append("Nessuna novita' trovata nel file importato. I database erano gia' allineati.")
        else:
            log.append("\nFusione completata e file aggiornati con successo!")
        return True, log

    def export_to_txt(self):
        with open(self.txt_filename, 'w', encoding='utf-8') as f:
            f.write("Hall of Fame di Dadillo\n\n")
            
            # Funzione per ordinamento: prima ori, poi argenti, poi bronzi, poi legni (tutti in ordine decrescente = chi ne ha di più sta in cima)
            # Poi ordina per media piazzamenti (somma piazzamenti >= 5 / numero tornei) decrescente (la media più bassa sta in cima)
            # e infine ordina per quantità di tornei giocati (per risolvere i parimerito) e per nome alfabetico.
            import functools
            
            def compare_db_players(a_item, b_item):
                name_a, data_a = a_item
                name_b, data_b = b_item
                
                m_a = data_a["medals"]
                m_b = data_b["medals"]
                
                if m_a['oro'] != m_b['oro']:
                    return (m_b['oro'] > m_a['oro']) - (m_b['oro'] < m_a['oro'])
                if m_a['argento'] != m_b['argento']:
                    return (m_b['argento'] > m_a['argento']) - (m_b['argento'] < m_a['argento'])
                if m_a['bronzo'] != m_b['bronzo']:
                    return (m_b['bronzo'] > m_a['bronzo']) - (m_b['bronzo'] < m_a['bronzo'])
                if m_a['legno'] != m_b['legno']:
                    return (m_b['legno'] > m_a['legno']) - (m_b['legno'] < m_a['legno'])
                
                # Calcolo media piazzamenti
                len_a = len(data_a['history'])
                len_b = len(data_b['history'])
                avg_a = data_a.get("placements_sum", 0) / len_a if len_a > 0 else 0
                avg_b = data_b.get("placements_sum", 0) / len_b if len_b > 0 else 0
                
                if avg_a != avg_b:
                    return (avg_a > avg_b) - (avg_a < avg_b)
                
                # Spareggio ulteriore: numero di partecipazioni
                if len_a != len_b:
                    return (len_b > len_a) - (len_b < len_a)
                    
                # Alfabetico
                return (name_a > name_b) - (name_a < name_b)

            sorted_players = sorted(self.players.items(), key=functools.cmp_to_key(compare_db_players))
            
            for name, p in sorted_players:
                m = p["medals"]
                
                # Livello 0: Nome
                f.write(f"{name}\n")
                
                # Livello 1: Medagliere e Intestazione Storico
                medals_str_parts = []
                if m['oro'] >= 1:
                    medals_str_parts.append(f"Oro {m['oro']}")
                if m['argento'] >= 1:
                    medals_str_parts.append(f"Argento {m['argento']}")
                if m['bronzo'] >= 1:
                    medals_str_parts.append(f"Bronzo {m['bronzo']}")
                if m['legno'] >= 1:
                    medals_str_parts.append(f"Legno {m['legno']}")
                
                if medals_str_parts:
                    medals_line = "  Medagliere: " + ", ".join(medals_str_parts) + "\n"
                else:
                    medals_line = "  Medagliere: Ancora nessuna medaglia\n"
                f.write(medals_line)
                
                num_tornei = len(p['history'])
                media = p.get('placements_sum', 0) / num_tornei if num_tornei > 0 else 0
                f.write(f"  Media Piazzamenti: {media:.2f} (Tornei giocati: {num_tornei})\n")
                
                f.write("  Storico Tornei:\n")
                
                # Livello 2: Tornei
                for h in p["history"]:
                    f.write(f"    {h}\n")
                
                f.write("\n")
