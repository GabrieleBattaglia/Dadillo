import os

from data import DATA_FILE, TournamentData


class MockChoice:
    def __init__(self, selection_str="", selection_idx=0):
        self._str = selection_str
        self._idx = selection_idx

    def GetStringSelection(self):
        return self._str

    def GetSelection(self):
        return self._idx


from standings import rank_tournament_players


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
    orig_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        t = TournamentData()
        t.title = "Torneo Golf Test"
        t.main_criterion = "Punti"
        t.score_direction = "Basso"
        t.tiebreaker_1 = "Scontro Diretto (Punti)"
        t.tiebreaker_2 = "Vittorie Totali"
        t.save()

        assert os.path.exists(DATA_FILE)

        t2 = TournamentData()
        loaded = t2.load()

        assert loaded is True
        assert t2.title == "Torneo Golf Test"
        assert t2.main_criterion == "Punti"
        assert t2.score_direction == "Basso"
        assert t2.tiebreaker_1 == "Scontro Diretto (Punti)"
        assert t2.tiebreaker_2 == "Vittorie Totali"
    finally:
        os.chdir(orig_dir)


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

    orig_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        db = PlayerDB()
        db.add_or_update_player(
            "Peppe",
            1,
            True,
            False,
            False,
            False,
            "Torneo Alfa",
            "2026-01-01",
            "2026-01-10",
        )
        db.add_or_update_player(
            "Selene",
            2,
            False,
            True,
            False,
            False,
            "Torneo Alfa",
            "2026-01-01",
            "2026-01-10",
        )
        db.save()

        # Verifica stato iniziale
        assert db.players["Peppe"]["medals"]["oro"] == 1
        assert db.players["Selene"]["medals"]["argento"] == 1

        # File esterno con gli stessi dati
        ext_path = "external_players.json"
        with open(ext_path, "w", encoding="utf-8") as f:
            json.dump(db.players, f, indent=4)

        # Fonde lo stesso file
        success, _log = db.merge_db(ext_path)
        assert success is True
        # I contatori NON devono raddoppiare!
        assert db.players["Peppe"]["medals"]["oro"] == 1
        assert db.players["Selene"]["medals"]["argento"] == 1
        assert len(db.players["Peppe"]["history"]) == 1
    finally:
        os.chdir(orig_dir)


def test_merge_db_fuzzy_matching_and_resolution(tmp_path):
    import json

    from data import PlayerDB

    orig_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        db = PlayerDB()
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
        ext_path = "ext_siddharta.json"
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
    finally:
        os.chdir(orig_dir)


if __name__ == "__main__":
    import pathlib
    import tempfile

    print("Esecuzione test_standings_ranking...")
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
    print("Tutti i test sono stati superati con successo!")
