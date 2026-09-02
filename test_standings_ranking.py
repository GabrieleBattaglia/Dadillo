import os
from pathlib import Path

from data import TournamentData
from standings import rank_tournament_players


class MockChoice:
    def __init__(self, selection_str="", selection_idx=0):
        self._str = selection_str
        self._idx = selection_idx

    def GetStringSelection(self):
        return self._str

    def GetSelection(self):
        return self._idx


class DummyStandingsHelper:
    def __init__(
        self,
        tourney,
        order_by="Vittorie",
        score_direction="Alto",
        tie1="Scontro Diretto (Punti)",
        tie2="Punti Totali",
        reverse=True,
    ):
        self.tourney = tourney
        self.order_by = order_by
        self.score_direction = score_direction
        self.tie1 = tie1
        self.tie2 = tie2
        self.reverse = reverse

    def sort_players(self):
        ranked = rank_tournament_players(
            self.tourney.players,
            self.tourney.played_matches,
            order_by=self.order_by,
            score_direction=self.score_direction,
            tiebreaker_1=self.tie1,
            tiebreaker_2=self.tie2,
            unplayed_matches=self.tourney.unplayed_matches,
            reverse=self.reverse,
        )
        return [item["name"] for item in ranked]


def test_tournament_json_persistence(tmp_path):
    # base_dir isola il test dai file di dati reali dell'applicazione
    base = str(tmp_path)
    t = TournamentData(base_dir=base)
    t.title = "Torneo Golf Test"
    t.main_criterion = "Punti"
    t.score_direction = "Basso"
    t.tiebreaker_1 = "Scontro Diretto (Punti)"
    t.tiebreaker_2 = "Vittorie Totali"
    t.save()

    assert os.path.exists(t.filename)
    assert os.path.dirname(t.filename) == base

    t2 = TournamentData(base_dir=base)
    loaded = t2.load()

    assert loaded is True
    assert t2.title == "Torneo Golf Test"
    assert t2.main_criterion == "Punti"
    assert t2.score_direction == "Basso"
    assert t2.tiebreaker_1 == "Scontro Diretto (Punti)"
    assert t2.tiebreaker_2 == "Vittorie Totali"


def test_ranking_primary_points_score_basso():
    t = TournamentData()
    # stats: [points, wins, draws, losses]
    t.players = {"Alice": [15, 2, 0, 0], "Bob": [5, 1, 0, 1], "Charlie": [25, 3, 0, 0]}
    # When score_direction == "Basso", lowest points wins (Bob: 5, Alice: 15, Charlie: 25)
    helper = DummyStandingsHelper(t, order_by="Punti", score_direction="Basso")
    ranked = helper.sort_players()
    assert ranked == ["Bob", "Alice", "Charlie"]


def test_ranking_primary_points_score_alto():
    t = TournamentData()
    t.players = {"Alice": [15, 2, 0, 0], "Bob": [5, 1, 0, 1], "Charlie": [25, 3, 0, 0]}
    # When score_direction == "Alto", highest points wins (Charlie: 25, Alice: 15, Bob: 5)
    helper = DummyStandingsHelper(t, order_by="Punti", score_direction="Alto")
    ranked = helper.sort_players()
    assert ranked == ["Charlie", "Alice", "Bob"]


def test_ranking_vittorie_primary_score_basso_tiebreak():
    t = TournamentData()
    # Alice and Bob both have 2 wins.
    # Alice has 100 points, Bob has 30 points. Charlie has 1 win, 10 points.
    t.players = {
        "Alice": [100, 2, 0, 0],
        "Bob": [30, 2, 0, 0],
        "Charlie": [10, 1, 0, 1],
    }
    # Primary: Vittorie. Tiebreaker 2: Punti Totali with score_direction = Basso.
    # Order: 2 wins first -> Bob (30 pts) beats Alice (100 pts). Then 1 win -> Charlie.
    helper = DummyStandingsHelper(
        t,
        order_by="Vittorie",
        score_direction="Basso",
        tie1="Nessuno",
        tie2="Punti Totali",
    )
    ranked = helper.sort_players()
    assert ranked == ["Bob", "Alice", "Charlie"]


def test_head_to_head_tiebreak_score_basso():
    t = TournamentData()
    t.players = {"Alice": [20, 1, 0, 0], "Bob": [20, 1, 0, 0]}
    # Played match 1: Alice vs Bob, Alice wins result '1', pt1=5, pt2=15.
    t.played_matches = {1: ["Alice", "Bob", "1", 5, 5, 15]}
    # Scontro Diretto (Punti) with score_direction = Basso:
    # Alice scored 5 pts in H2H, Bob scored 15 pts in H2H. Lower is better -> Alice (5 pts) wins tiebreak!
    helper = DummyStandingsHelper(
        t,
        order_by="Vittorie",
        score_direction="Basso",
        tie1="Scontro Diretto (Punti)",
        tie2="Nessuno",
    )
    ranked = helper.sort_players()
    assert ranked == ["Alice", "Bob"]


def test_setup_players_db_selection_behavior():
    import wx

    from dialogs import SetupPlayersDialog

    app = wx.App(False)
    dlg = SetupPlayersDialog(None, existing_players=["Dario"])

    # Pre-populate DB players listbox for testing
    dlg.all_db_players = ["Alice", "Bob", "Charlie"]
    dlg.list_db_players.Set(["Alice", "Bob", "Charlie"])
    dlg.update_db_label()

    assert "3 disponibili" in dlg.lbl_db.GetLabel()

    # Simulate selecting first item "Alice" (index 0) and adding from DB
    dlg.add_from_db(0)

    assert "Alice" in dlg.players
    assert "2 disponibili" in dlg.lbl_db.GetLabel()
    assert dlg.list_db_players.GetCount() == 2
    assert dlg.list_db_players.GetString(0) == "Bob"
    assert dlg.list_db_players.GetSelection() == 0

    # Add Bob (now index 0)
    dlg.add_from_db(0)
    assert "1 disponibili" in dlg.lbl_db.GetLabel()
    assert dlg.list_db_players.GetCount() == 1
    assert dlg.list_db_players.GetString(0) == "Charlie"

    # Add Charlie (index 0, now list becomes empty)
    dlg.add_from_db(0)
    assert "0 disponibili" in dlg.lbl_db.GetLabel()
    assert dlg.list_db_players.GetCount() == 0

    dlg.Destroy()
    app.Destroy()


def test_ranking_3_way_tie_head_to_head_wins():
    t = TournamentData()
    # 3 players tied on primary criterion: 2 wins each
    t.players = {
        "Alice": [20, 2, 0, 1],
        "Bob": [20, 2, 0, 1],
        "Charlie": [20, 2, 0, 1],
        "David": [0, 0, 0, 3],
    }
    # Matches between Alice, Bob, Charlie:
    # Alice beat Bob (res '1')
    # Alice beat Charlie (res '1')
    # Bob beat Charlie (res '1')
    # Everyone beat David
    t.played_matches = {
        1: ["Alice", "Bob", "1", 10, 10, 0],
        2: ["Alice", "Charlie", "1", 10, 10, 0],
        3: ["Bob", "Charlie", "1", 10, 10, 0],
        4: ["David", "Alice", "2", 0, 0, 0],
        5: ["David", "Bob", "2", 0, 0, 0],
        6: ["David", "Charlie", "2", 0, 0, 0],
    }
    # In the mini-league of {Alice, Bob, Charlie}:
    # Alice has 2 wins, Bob has 1 win, Charlie has 0 wins.
    helper = DummyStandingsHelper(
        t,
        order_by="Vittorie",
        tie1="Scontro Diretto (Vittorie)",
        tie2="Punti Totali",
    )
    ranked = helper.sort_players()
    assert ranked == ["Alice", "Bob", "Charlie", "David"]


def test_ranking_3_way_cyclic_tie_resolves_to_tiebreaker2():
    t = TournamentData()
    # 3 players tied on 2 wins each: Alice, Bob, Charlie
    # Cyclic head to head: Alice beats Bob, Bob beats Charlie, Charlie beats Alice.
    # Mini-league wins: Alice (1), Bob (1), Charlie (1) -> perfectly tied!
    # Tiebreaker 2: Punti Totali (Alice 50 pts, Bob 40 pts, Charlie 30 pts)
    t.players = {
        "Alice": [50, 2, 0, 1],
        "Bob": [40, 2, 0, 1],
        "Charlie": [30, 2, 0, 1],
    }
    t.played_matches = {
        1: ["Alice", "Bob", "1", 10, 10, 0],
        2: ["Bob", "Charlie", "1", 10, 10, 0],
        3: ["Charlie", "Alice", "1", 10, 10, 0],
    }
    helper = DummyStandingsHelper(
        t,
        order_by="Vittorie",
        tie1="Scontro Diretto (Vittorie)",
        tie2="Punti Totali",
    )
    ranked = helper.sort_players()
    assert ranked == ["Alice", "Bob", "Charlie"]


def test_ranking_4_way_tie_partial_recursive_resolution():
    t = TournamentData()
    # 4 players tied on primary criterion: 3 wins each
    t.players = {
        "A": [30, 3, 0, 1],
        "B": [30, 3, 0, 1],
        "C": [25, 3, 0, 1],  # C has more total points than D
        "D": [15, 3, 0, 1],
    }
    # Matches between A, B, C, D:
    # A beat B, C, D (3 mini wins)
    # B beat C, D (2 mini wins)
    # C and D drew with each other (0 mini wins, 1 draw each)
    t.played_matches = {
        1: ["A", "B", "1", 10, 10, 0],
        2: ["A", "C", "1", 10, 10, 0],
        3: ["A", "D", "1", 10, 10, 0],
        4: ["B", "C", "1", 10, 10, 0],
        5: ["B", "D", "1", 10, 10, 0],
        6: ["C", "D", "3", 10, 5, 5],
    }
    # 1. Mini-league {A, B, C, D} -> A (3 wins) = 1st, B (2 wins) = 2nd, {C, D} (0 wins) = tied.
    # 2. Subgroup {C, D} is re-evaluated:
    #    - H2H {C, D}: match 6 was a draw (0 wins each) -> tied on tiebreaker 1.
    #    - tiebreaker 2 (Punti Totali): C has 25 pts, D has 15 pts -> C beats D.
    helper = DummyStandingsHelper(
        t,
        order_by="Vittorie",
        tie1="Scontro Diretto (Vittorie)",
        tie2="Punti Totali",
    )
    ranked = helper.sort_players()
    assert ranked == ["A", "B", "C", "D"]


def test_ranking_3_way_tie_score_basso_mini_league():
    t = TournamentData()
    # 3 players tied with 1 win each
    t.players = {
        "Alice": [20, 1, 0, 1],
        "Bob": [20, 1, 0, 1],
        "Charlie": [20, 1, 0, 1],
    }
    # Matches between them with points:
    # Match 1: Alice vs Bob -> Alice scores 2 pts, Bob scores 8 pts (res '1')
    # Match 2: Bob vs Charlie -> Bob scores 3 pts, Charlie scores 9 pts (res '1')
    # Match 3: Charlie vs Alice -> Charlie scores 4 pts, Alice scores 7 pts (res '1')
    # Sum of mini-league points:
    # Alice: 2 + 7 = 9 pts
    # Bob: 8 + 3 = 11 pts
    # Charlie: 9 + 4 = 13 pts
    # With score_direction = "Basso", lowest points wins: Alice (9) < Bob (11) < Charlie (13)
    t.played_matches = {
        1: ["Alice", "Bob", "1", 2, 2, 8],
        2: ["Bob", "Charlie", "1", 3, 3, 9],
        3: ["Charlie", "Alice", "1", 4, 4, 7],
    }
    helper = DummyStandingsHelper(
        t,
        order_by="Vittorie",
        score_direction="Basso",
        tie1="Scontro Diretto (Punti)",
        tie2="Nessuno",
    )
    ranked = helper.sort_players()
    assert ranked == ["Alice", "Bob", "Charlie"]


def test_ranking_total_tie_alphabetical_fallback():
    t = TournamentData()
    # Alice, Bob, Charlie have identical stats and drew with each other
    t.players = {
        "Charlie": [10, 0, 2, 0],
        "Alice": [10, 0, 2, 0],
        "Bob": [10, 0, 2, 0],
    }
    t.played_matches = {
        1: ["Alice", "Bob", "3", 10, 5, 5],
        2: ["Bob", "Charlie", "3", 10, 5, 5],
        3: ["Charlie", "Alice", "3", 10, 5, 5],
    }
    helper = DummyStandingsHelper(
        t,
        order_by="Punti",
        tie1="Scontro Diretto (Punti)",
        tie2="Vittorie Totali",
    )
    ranked = helper.sort_players()
    assert ranked == ["Alice", "Bob", "Charlie"]


def test_merge_db_no_duplicate_medals(tmp_path):
    import json

    from data import PlayerDB

    base = str(tmp_path)
    db = PlayerDB(base_dir=base)
    db.add_or_update_player("Peppe", 1, "Torneo Alfa", "2026-01-01", "2026-01-10")
    db.add_or_update_player("Selene", 2, "Torneo Alfa", "2026-01-01", "2026-01-10")
    db.save()

    # Verifica stato iniziale
    assert db.players["Peppe"]["medals"]["oro"] == 1
    assert db.players["Selene"]["medals"]["argento"] == 1

    # File esterno con gli stessi dati
    ext_path = os.path.join(base, "external_players.json")
    with open(ext_path, "w", encoding="utf-8") as f:
        json.dump(db.players, f, indent=4)

    # Fonde lo stesso file
    success, _log = db.merge_db(ext_path)
    assert success is True
    # I contatori NON devono raddoppiare!
    assert db.players["Peppe"]["medals"]["oro"] == 1
    assert db.players["Selene"]["medals"]["argento"] == 1
    assert len(db.players["Peppe"]["history"]) == 1


def test_merge_db_fuzzy_matching_and_resolution(tmp_path):
    import json

    from data import PlayerDB

    base = str(tmp_path)
    db = PlayerDB(base_dir=base)
    db.players["Siddharta"] = {
        "medals": {"oro": 0, "argento": 0, "bronzo": 1, "legno": 0},
        "history": ["3° in Farkle Bonus - 2026-03-17 - 2026-04-20"],
        "placements_sum": 0,
    }
    db.save()

    # File esterno con nome simile 'Siddharta33' e un nuovo torneo
    ext_data = {
        "Siddharta33": {
            "medals": {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0},
            "history": ["10° in Yatzee con Bonus - 2026-05-01 - 2026-05-30"],
            "placements_sum": 10,
        }
    }
    ext_path = os.path.join(base, "ext_siddharta.json")
    with open(ext_path, "w", encoding="utf-8") as f:
        json.dump(ext_data, f, indent=4)

    # Simula il resolver che conferma che sono la stessa persona e sceglie 'Siddharta33'
    resolved = []

    def mock_resolver(ext_name, candidate_name):
        resolved.append((ext_name, candidate_name))
        return True, "Siddharta33"

    success, _log = db.merge_db(ext_path, interactive_resolver=mock_resolver)
    assert success is True
    assert len(resolved) == 1
    assert resolved[0] == ("Siddharta33", "Siddharta")

    # Verifica che il giocatore sia stato unificato sotto 'Siddharta33'
    assert "Siddharta33" in db.players
    assert "Siddharta" not in db.players
    p = db.players["Siddharta33"]
    assert len(p["history"]) == 2
    assert p["medals"]["bronzo"] == 1
    assert p["placements_sum"] == 10


def test_format_date_extended():
    import datetime

    from data import format_date_extended

    # Stringhe ISO
    assert format_date_extended("2026-08-20") == "giovedì 20 agosto 2026"
    assert format_date_extended("2026-08-20 17:40:05") == "giovedì 20 agosto 2026"
    assert format_date_extended("2026-03-17") == "martedì 17 marzo 2026"
    assert format_date_extended("2026-04-20") == "lunedì 20 aprile 2026"
    assert format_date_extended("2026-05-01") == "venerdì 1 maggio 2026"
    assert format_date_extended("2026-08-01") == "sabato 1 agosto 2026"
    assert format_date_extended("2026-08-15") == "sabato 15 agosto 2026"

    # Datetime objects
    dt = datetime.date(2026, 8, 20)
    assert format_date_extended(dt) == "giovedì 20 agosto 2026"

    # Stringhe già in formato esteso o con nome mese
    assert format_date_extended("giovedì 20 agosto 2026") == "giovedì 20 agosto 2026"
    assert format_date_extended("1 agosto 2026") == "sabato 1 agosto 2026"


def test_regola_pareggi_unica_per_i_record_vecchi():
    from data import split_match_points
    from standings import _extract_match_details

    # Record nel vecchio formato a quattro elementi, pareggio da 10 punti
    record = ["Alice", "Bob", "3", 10]

    assert split_match_points("3", 10, "Metà ciascuno") == (5.0, 5.0)
    assert split_match_points("3", 10, "Nessun Punto") == (0, 0)
    assert split_match_points("3", 10, "Punti Pieni a Entrambi") == (10, 10)
    assert split_match_points("1", 10, "Metà ciascuno") == (10, 0)
    assert split_match_points("2", 10, "Metà ciascuno") == (0, 10)

    # La classifica applica la stessa regola, non piu' una sua
    _, _, _, pt1, pt2 = _extract_match_details(record, "Nessun Punto")
    assert (pt1, pt2) == (0, 0)
    _, _, _, pt1, pt2 = _extract_match_details(record, "Punti Pieni a Entrambi")
    assert (pt1, pt2) == (10, 10)


def test_migrazione_record_partita_al_formato_completo(tmp_path):
    import json

    base = str(tmp_path)
    t = TournamentData(base_dir=base)
    t.title = "Torneo vecchio"
    t.draw_points_split = "Nessun Punto"
    t.players = {"Alice": [0, 0, 1, 0], "Bob": [0, 0, 1, 0]}
    t.save()

    # Riscriviamo il file con una partita nel vecchio formato a 4 elementi
    with open(t.filename, encoding="utf-8") as f:
        salvato = json.load(f)
    salvato["played_matches"] = {"1": ["Alice", "Bob", "3", 10]}
    with open(t.filename, "w", encoding="utf-8") as f:
        json.dump(salvato, f)

    t2 = TournamentData(base_dir=base)
    assert t2.load() is True
    record = t2.played_matches[1]
    assert len(record) == 6
    # La conversione usa la regola del torneo, qui Nessun Punto
    assert record[4] == 0
    assert record[5] == 0


def test_parita_irrisolta_viene_segnalata():
    from standings import rank_tournament_players

    # Due giocatori identici in tutto: nessuno spareggio puo' separarli
    players = {"Anna": [10, 2, 0, 1], "Bruno": [10, 2, 0, 1]}
    ranked = rank_tournament_players(
        players,
        {},
        order_by="Vittorie",
        tiebreaker_1="Nessuno",
        tiebreaker_2="Nessuno",
    )
    nomi = [r["name"] for r in ranked]
    assert nomi == ["Anna", "Bruno"]
    assert ranked[0]["tied_with"] == ["Bruno"]
    assert ranked[1]["tied_with"] == ["Anna"]


def test_media_piazzamenti_distingue_i_casi_senza_dati():
    from data import (
        MEDIA_NON_DISPONIBILE,
        SOLO_PODI,
        hall_of_fame_sort_key,
        placement_stats,
    )

    solo_podi = {
        "medals": {"oro": 1, "argento": 0, "bronzo": 0, "legno": 0},
        "history": ["1° in Torneo Uno - a - b"],
        "placements_sum": 0,
    }
    con_piazzamenti = {
        "medals": {"oro": 1, "argento": 0, "bronzo": 0, "legno": 0},
        "history": ["1° in Torneo Uno - a - b", "8° in Torneo Due - c - d"],
        "placements_sum": 8,
    }
    storico_illeggibile = {
        "medals": {"oro": 1, "argento": 0, "bronzo": 0, "legno": 0},
        "history": ["appunti presi a mano"],
        "placements_sum": 0,
    }

    assert placement_stats(solo_podi)[1] == SOLO_PODI
    assert placement_stats(solo_podi)[2] == "solo podi"
    assert placement_stats(con_piazzamenti)[2] == "4.00"
    assert placement_stats(storico_illeggibile)[1] == MEDIA_NON_DISPONIBILE
    assert placement_stats(storico_illeggibile)[2] == "non disponibile"

    # A parita' di medaglie chi ha solo podi sta davanti, e uno storico
    # illeggibile non deve piu' scavalcare chi ha piazzamenti veri.
    ordinati = sorted(
        [
            ("Ignoto", storico_illeggibile),
            ("Piazzato", con_piazzamenti),
            ("Podista", solo_podi),
        ],
        key=lambda item: hall_of_fame_sort_key(*item),
    )
    assert [nome for nome, _ in ordinati] == ["Podista", "Piazzato", "Ignoto"]


def test_ricerca_coppia_in_entrambi_gli_ordini():
    from main_window import MainFrame

    filtro = MainFrame.match_filter
    testo = "(3) Anna vs Bruno"
    assert filtro(testo, "Anna", "Bruno", "anna bruno") is True
    # La partita di ritorno va trovata anche cercando i nomi al contrario
    assert filtro(testo, "Anna", "Bruno", "bruno anna") is True
    assert filtro(testo, "Anna", "Bruno", "anna") is True
    assert filtro(testo, "Anna", "Bruno", "carla") is False
    assert filtro(testo, "Anna", "Bruno", "") is True


def test_duplicati_storico_con_titoli_simili(tmp_path):
    from data import PlayerDB

    db = PlayerDB(base_dir=str(tmp_path))
    assert (
        db.add_or_update_player("Anna", 1, "Torneo", "2026-01-01", "2026-01-10") is True
    )
    # Stesso titolo e stessa data di inizio: e' lo stesso torneo, va scartato
    assert (
        db.add_or_update_player("Anna", 1, "Torneo", "2026-01-01", "2026-01-10")
        is False
    )
    # Titolo che contiene il primo come sottostringa: e' un torneo diverso
    assert (
        db.add_or_update_player(
            "Anna", 2, "Torneo di Natale", "2026-01-01", "2026-01-10"
        )
        is True
    )
    assert len(db.players["Anna"]["history"]) == 2


def test_classifica_leggibile_da_screen_reader(tmp_path):
    import wx

    from data import SettingsData
    from standings import StandingsPanel

    base = str(tmp_path)
    t = TournamentData(base_dir=base)
    t.title = "Torneo di prova"
    t.comment = "Che vinca il piu' devoto"
    t.start_date = "2026-08-20T10:00:00+02:00"
    t.end_date = "2026-08-22T18:30:00+02:00"
    # Due partite giocate: Marco vince la prima, la seconda finisce pari
    t.players = {"Marco": [12, 1, 1, 0], "Anna": [9, 0, 1, 1]}
    t.played_matches = {
        1: ["Marco", "Anna", "1", 3, 3, 0],
        2: ["Anna", "Marco", "3", 1, 1, 1],
    }

    app = wx.App(False)
    frame = wx.Frame(None)
    panel = StandingsPanel(frame, t, SettingsData(base_dir=base), is_final=True)
    testo = panel.txt_display.GetValue()
    righe = testo.split("\n")
    frame.Destroy()
    app.Destroy()

    # Nessun separatore grafico, nessuna riga vuota, nessuna emoji
    assert "---" not in testo
    assert "===" not in testo
    assert "___" not in testo
    assert all(r.strip() != "" for r in righe)
    for emoji in ("🥇", "🥈", "🥉", "🪵"):
        assert emoji not in testo

    # Una riga per giocatore, con la lettera davanti a ogni valore, e la
    # legenda che spiega le lettere. A torneo concluso le giocate si omettono.
    assert "Legenda: punti(T), vittorie(V), pareggi(P), sconfitte(S)." in righe
    assert "1. Marco, oro. T12 V1 P1 S0" in righe
    assert not any(r.startswith("  Giocate") for r in righe)
    # La media dei pareggi ora viene calcolata davvero
    assert any("Media punti per pareggio" in r for r in righe)


def test_giocate_solo_se_il_torneo_non_e_concluso(tmp_path):
    import wx

    from data import SettingsData
    from standings import StandingsPanel

    base = str(tmp_path)
    settings = SettingsData(base_dir=base)

    def testo_classifica(unplayed, is_final):
        t = TournamentData(base_dir=base)
        t.title = "Torneo di prova"
        t.start_date = "2026-09-01T10:00:00+02:00"
        t.players = {"Marco": [3, 1, 0, 0], "Anna": [0, 0, 0, 1]}
        t.played_matches = {1: ["Marco", "Anna", "1", 3, 3, 0]}
        t.unplayed_matches = unplayed
        frame = wx.Frame(None)
        panel = StandingsPanel(frame, t, settings, is_final=is_final)
        testo = panel.txt_display.GetValue()
        frame.Destroy()
        return testo

    app = wx.App(False)

    # Torneo concluso aperto con Ctrl+L, che chiede la classifica parziale:
    # le partite giocate sono per forza tutte, non vanno ripetute su ogni riga
    testo = testo_classifica({}, is_final=False)
    assert "Classifica finale" in testo
    assert "giocate(G)" not in testo
    assert "G1/1" not in testo
    assert "(Provvisoria)" not in testo

    # Torneo ancora in corso: le giocate servono e la durata e' provvisoria
    testo = testo_classifica({2: ["Anna", "Marco"]}, is_final=False)
    assert "Classifica parziale" in testo
    assert "giocate(G)" in testo
    assert "G1/2" in testo
    assert "(Provvisoria)" in testo

    app.Destroy()


def test_strisce_con_giocatore_ritirato():
    from standings import calculate_streaks

    # Alice e' stata ritirata: non e' piu' fra i partecipanti, ma le sue
    # partite, comprese le vittorie a tavolino, restano negli archivi.
    active = {"Bob": [3, 1, 0, 1], "Carla": [0, 0, 0, 1]}
    played = {
        1: ["Alice", "Bob", "1", 3, 3, 0],
        2: ["Bob", "Carla", "1", 3, 3, 0],
        3: ["Alice", "Bob", "2", 0],
    }

    strikes = calculate_streaks(active, played)

    # Nessun errore, e in classifica compaiono solo i giocatori ancora in gara
    assert set(strikes) == {"Bob", "Carla"}
    assert strikes["Bob"] == 2
    assert strikes["Carla"] == 0


def test_criterio_punti_totali_viene_riconosciuto():
    from data import normalize_choice, normalize_main_criterion

    # Vecchia etichetta della finestra Regole
    assert normalize_main_criterion("Punti Totali") == "Punti"
    # Valore gia' corretto
    assert normalize_main_criterion("Punti") == "Punti"
    # Criterio perduto da una conferma delle Regole: si torna al predefinito
    assert normalize_main_criterion("") == "Vittorie"
    assert normalize_main_criterion(None) == "Vittorie"
    assert normalize_main_criterion("Qualcosa di ignoto") == "Vittorie"
    assert normalize_choice("Nessuno", ("Punti Totali", "Nessuno")) == "Nessuno"
    assert normalize_choice("boh", ("Punti Totali", "Nessuno")) == "Punti Totali"


def test_criterio_a_punti_sopravvive_al_salvataggio(tmp_path):
    import json

    base = str(tmp_path)
    t = TournamentData(base_dir=base)
    t.title = "Torneo a penalita'"
    t.main_criterion = "Punti"
    t.save()

    # Un file scritto da una versione precedente con l'etichetta vecchia
    with open(t.filename, encoding="utf-8") as f:
        salvato = json.load(f)
    salvato["main_criterion"] = "Punti Totali"
    with open(t.filename, "w", encoding="utf-8") as f:
        json.dump(salvato, f)

    t2 = TournamentData(base_dir=base)
    assert t2.load() is True
    assert t2.main_criterion == "Punti"

    # E un file in cui il criterio era stato azzerato
    salvato["main_criterion"] = ""
    with open(t.filename, "w", encoding="utf-8") as f:
        json.dump(salvato, f)
    t3 = TournamentData(base_dir=base)
    assert t3.load() is True
    assert t3.main_criterion == "Vittorie"


def test_durata_torneo_con_fuso_orario():
    import datetime

    from data import now_timestamp, parse_timestamp

    # Formato nuovo, con fuso: la durata deve essere quella reale
    adesso = datetime.datetime.now(datetime.timezone.utc).astimezone()
    inizio = (adesso - datetime.timedelta(minutes=10)).replace(microsecond=0)
    dt_inizio = parse_timestamp(inizio.isoformat())
    assert dt_inizio is not None
    minuti = (adesso - dt_inizio).total_seconds() / 60
    assert 9 <= minuti <= 11

    # Vecchio formato senza fuso: va letto come ora locale, non come UTC
    testo_vecchio = inizio.strftime("%Y-%m-%d %H:%M:%S")
    dt_vecchio = parse_timestamp(testo_vecchio)
    assert dt_vecchio is not None
    minuti_vecchio = (adesso - dt_vecchio).total_seconds() / 60
    assert 9 <= minuti_vecchio <= 11

    # Il timestamp generato ora e' rileggibile e porta con se' il fuso
    riletto = parse_timestamp(now_timestamp())
    assert riletto is not None
    assert riletto.tzinfo is not None

    # Valori non interpretabili non fanno saltare nulla
    assert parse_timestamp("") is None
    assert parse_timestamp("non una data") is None


def test_atomic_write_conserva_la_versione_precedente(tmp_path):
    from data import atomic_write_text

    percorso = os.path.join(str(tmp_path), "prova.txt")
    atomic_write_text(percorso, "primo contenuto")
    assert Path(percorso).read_text(encoding="utf-8") == "primo contenuto"
    # Alla prima scrittura non esiste nulla da conservare
    assert not os.path.exists(percorso + ".bak")

    atomic_write_text(percorso, "secondo contenuto")
    assert Path(percorso).read_text(encoding="utf-8") == "secondo contenuto"
    assert Path(percorso + ".bak").read_text(encoding="utf-8") == "primo contenuto"

    # Nessun file temporaneo lasciato indietro
    residui = [n for n in os.listdir(str(tmp_path)) if n.startswith(".dadillo_")]
    assert residui == []


def test_torneo_danneggiato_non_viene_scambiato_per_assente(tmp_path):
    from data import DataFileError

    base = str(tmp_path)
    t = TournamentData(base_dir=base)
    with open(t.filename, "w", encoding="utf-8") as f:
        f.write("{questo non e' JSON valido")

    try:
        t.load()
        raise AssertionError("il caricamento doveva fallire con DataFileError")
    except DataFileError as e:
        # Una copia del file danneggiato deve essere stata messa da parte
        assert e.quarantine_path is not None
        assert os.path.exists(e.quarantine_path)
        # L'originale non viene toccato
        assert os.path.exists(t.filename)


def test_torneo_con_struttura_non_valida_viene_rifiutato(tmp_path):
    import json

    from data import DataFileError

    base = str(tmp_path)
    t = TournamentData(base_dir=base)
    # JSON valido ma con statistiche giocatore incomplete
    with open(t.filename, "w", encoding="utf-8") as f:
        json.dump({"title": "Rotto", "players": {"Alice": [0, 0]}}, f)

    try:
        t.load()
        raise AssertionError("la validazione doveva rifiutare i dati")
    except DataFileError:
        pass


def test_archivio_giocatori_danneggiato_non_viene_sovrascritto(tmp_path):
    from data import PlayerDB, SaveError

    base = str(tmp_path)
    percorso = os.path.join(base, "Dadillo_players.json")
    with open(percorso, "w", encoding="utf-8") as f:
        f.write("archivio rovinato, non JSON")

    db = PlayerDB(base_dir=base)
    assert db.load_error is not None
    assert db.players == {}

    # Salvare ora cancellerebbe la Hall of Fame: deve essere rifiutato
    try:
        db.save()
        raise AssertionError("il salvataggio doveva essere rifiutato")
    except SaveError:
        pass
    try:
        db.export_to_txt()
        raise AssertionError("l'esportazione doveva essere rifiutata")
    except SaveError:
        pass

    # Il file originale e' ancora li', intatto
    assert Path(percorso).read_text(encoding="utf-8") == "archivio rovinato, non JSON"


def test_merge_db_non_sovrascrive_un_discepolo_esistente(tmp_path):
    import json

    from data import PlayerDB

    base = str(tmp_path)
    db = PlayerDB(base_dir=base)
    db.players["Marco"] = {
        "medals": {"oro": 1, "argento": 0, "bronzo": 0, "legno": 0},
        "history": ["1° in Torneo Uno - 2026-01-01 - 2026-01-10"],
        "placements_sum": 0,
    }
    db.players["marco1990"] = {
        "medals": {"oro": 0, "argento": 1, "bronzo": 0, "legno": 0},
        "history": ["2° in Torneo Due - 2026-02-01 - 2026-02-10"],
        "placements_sum": 0,
    }
    db.save()

    ext_data = {
        "Marco90": {
            "medals": {"oro": 0, "argento": 0, "bronzo": 1, "legno": 0},
            "history": ["3° in Torneo Tre - 2026-03-01 - 2026-03-10"],
            "placements_sum": 0,
        }
    }
    ext_path = os.path.join(base, "ext_marco.json")
    with open(ext_path, "w", encoding="utf-8") as f:
        json.dump(ext_data, f, indent=4)

    # L'utente conferma che Marco90 e il candidato locale sono la stessa persona
    # e sceglie come nome definitivo 'Marco', che pero' esiste gia' in archivio.
    def resolver(ext_name, candidate_name):
        return True, "Marco"

    success, _log = db.merge_db(ext_path, interactive_resolver=resolver)
    assert success is True

    # Nessuno storico deve andare perduto nella fusione: ne' quello del
    # discepolo di destinazione, ne' quello del candidato assorbito.
    storico = db.players["Marco"]["history"]
    assert any("Torneo Uno" in v for v in storico)
    assert any("Torneo Due" in v for v in storico)
    assert any("Torneo Tre" in v for v in storico)
    assert db.players["Marco"]["medals"]["oro"] == 1
    assert db.players["Marco"]["medals"]["argento"] == 1
    assert db.players["Marco"]["medals"]["bronzo"] == 1
    assert "marco1990" not in db.players


if __name__ == "__main__":
    import pathlib
    import tempfile

    print("Esecuzione test_standings_ranking...")
    test_format_date_extended()
    test_ranking_primary_points_score_basso()
    test_ranking_primary_points_score_alto()
    test_ranking_vittorie_primary_score_basso_tiebreak()
    test_head_to_head_tiebreak_score_basso()
    test_ranking_3_way_tie_head_to_head_wins()
    test_ranking_3_way_cyclic_tie_resolves_to_tiebreaker2()
    test_ranking_4_way_tie_partial_recursive_resolution()
    test_ranking_3_way_tie_score_basso_mini_league()
    test_ranking_total_tie_alphabetical_fallback()
    test_tournament_json_persistence(pathlib.Path(tempfile.mkdtemp()))
    test_setup_players_db_selection_behavior()
    test_merge_db_no_duplicate_medals(pathlib.Path(tempfile.mkdtemp()))
    test_merge_db_fuzzy_matching_and_resolution(pathlib.Path(tempfile.mkdtemp()))
    test_regola_pareggi_unica_per_i_record_vecchi()
    test_migrazione_record_partita_al_formato_completo(pathlib.Path(tempfile.mkdtemp()))
    test_parita_irrisolta_viene_segnalata()
    test_media_piazzamenti_distingue_i_casi_senza_dati()
    test_ricerca_coppia_in_entrambi_gli_ordini()
    test_duplicati_storico_con_titoli_simili(pathlib.Path(tempfile.mkdtemp()))
    test_classifica_leggibile_da_screen_reader(pathlib.Path(tempfile.mkdtemp()))
    test_giocate_solo_se_il_torneo_non_e_concluso(pathlib.Path(tempfile.mkdtemp()))
    test_strisce_con_giocatore_ritirato()
    test_criterio_punti_totali_viene_riconosciuto()
    test_criterio_a_punti_sopravvive_al_salvataggio(pathlib.Path(tempfile.mkdtemp()))
    test_durata_torneo_con_fuso_orario()
    test_atomic_write_conserva_la_versione_precedente(pathlib.Path(tempfile.mkdtemp()))
    test_torneo_danneggiato_non_viene_scambiato_per_assente(
        pathlib.Path(tempfile.mkdtemp())
    )
    test_torneo_con_struttura_non_valida_viene_rifiutato(
        pathlib.Path(tempfile.mkdtemp())
    )
    test_archivio_giocatori_danneggiato_non_viene_sovrascritto(
        pathlib.Path(tempfile.mkdtemp())
    )
    test_merge_db_non_sovrascrive_un_discepolo_esistente(
        pathlib.Path(tempfile.mkdtemp())
    )
    print("Tutti i test sono stati superati con successo!")
