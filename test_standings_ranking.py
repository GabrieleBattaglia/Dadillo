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
        self.cb_order = MockChoice(order_by)
        self.cb_score_dir = MockChoice(
            "Punteggio più alto"
            if score_direction == "Alto"
            else "Punteggio più basso",
            0 if score_direction == "Alto" else 1,
        )
        self.cb_tie1 = MockChoice(tie1)
        self.cb_tie2 = MockChoice(tie2)
        self.cb_dir = MockChoice("Discendente", 0 if reverse else 1)

    def _calculate_head_to_head(self, p1_name, p2_name):
        score_a = 0
        score_b = 0
        wins_a = 0
        wins_b = 0

        for m_id, data in self.tourney.played_matches.items():
            if len(data) >= 6:
                mn1, mn2, mres, mpts, pt1, pt2 = data[:6]
            else:
                mn1, mn2, mres, mpts = data[:4]
                if mres == "1":
                    pt1, pt2 = mpts, 0
                elif mres == "2":
                    pt1, pt2 = 0, mpts
                else:
                    pt1, pt2 = mpts / 2.0, mpts / 2.0

            if mn1 == p1_name and mn2 == p2_name:
                score_a += pt1
                score_b += pt2
                if mres == "1":
                    wins_a += 1
                elif mres == "2":
                    wins_b += 1
            elif mn1 == p2_name and mn2 == p1_name:
                score_b += pt1
                score_a += pt2
                if mres == "1":
                    wins_b += 1
                elif mres == "2":
                    wins_a += 1

        return score_a, score_b, wins_a, wins_b

    def sort_players(self):
        order_by = self.cb_order.GetStringSelection()
        score_direction = "Alto" if self.cb_score_dir.GetSelection() == 0 else "Basso"
        tiebreaker_1 = self.cb_tie1.GetStringSelection()
        tiebreaker_2 = self.cb_tie2.GetStringSelection()
        reverse = self.cb_dir.GetSelection() == 0

        unplayed_counts = {name: 0 for name in self.tourney.players.keys()}
        for m_id, (p1, p2) in self.tourney.unplayed_matches.items():
            if p1 in unplayed_counts:
                unplayed_counts[p1] += 1
            if p2 in unplayed_counts:
                unplayed_counts[p2] += 1

        flat = []
        for name, stats in self.tourney.players.items():
            played = stats[1] + stats[2] + stats[3]
            total = played + unplayed_counts[name]
            played_str = f"{played}/{total}"

            flat.append(
                {
                    "name": name,
                    "points": stats[0],
                    "wins": stats[1],
                    "draws": stats[2],
                    "losses": stats[3],
                    "played_str": played_str,
                }
            )

        import functools

        def compare_players(a, b):
            if order_by == "Vittorie":
                if a["wins"] != b["wins"]:
                    return (a["wins"] > b["wins"]) - (a["wins"] < b["wins"])
            elif order_by == "Punti":
                if a["points"] != b["points"]:
                    if score_direction == "Basso":
                        return (b["points"] > a["points"]) - (b["points"] < a["points"])
                    else:
                        return (a["points"] > b["points"]) - (a["points"] < b["points"])
            elif order_by == "Sconfitte":
                if a["losses"] != b["losses"]:
                    return (b["losses"] > a["losses"]) - (b["losses"] < a["losses"])
            elif order_by == "Pareggi":
                if a["draws"] != b["draws"]:
                    return (a["draws"] > b["draws"]) - (a["draws"] < b["draws"])
            elif order_by == "Nome Giocatore":
                if a["name"].lower() != b["name"].lower():
                    return (b["name"].lower() > a["name"].lower()) - (
                        b["name"].lower() < a["name"].lower()
                    )

            if order_by != "Nome Giocatore" and tiebreaker_1 != "Nessuno":
                pts_a, pts_b, w_a, w_b = self._calculate_head_to_head(
                    a["name"], b["name"]
                )

                if "Punti" in tiebreaker_1:
                    if pts_a != pts_b:
                        if score_direction == "Basso":
                            return (pts_b > pts_a) - (pts_b < pts_a)
                        else:
                            return (pts_a > pts_b) - (pts_a < pts_b)
                elif "Vittorie" in tiebreaker_1:
                    if w_a != w_b:
                        return (w_a > w_b) - (w_a < w_b)

            if tiebreaker_2 != "Nessuno":
                if tiebreaker_2 == "Punti Totali" and order_by != "Punti":
                    if a["points"] != b["points"]:
                        if score_direction == "Basso":
                            return (b["points"] > a["points"]) - (
                                b["points"] < a["points"]
                            )
                        else:
                            return (a["points"] > b["points"]) - (
                                a["points"] < b["points"]
                            )
                elif tiebreaker_2 == "Vittorie Totali" and order_by != "Vittorie":
                    if a["wins"] != b["wins"]:
                        return (a["wins"] > b["wins"]) - (a["wins"] < b["wins"])

            name_cmp = (a["name"] > b["name"]) - (a["name"] < b["name"])
            if reverse:
                return -name_cmp
            return name_cmp

        flat.sort(key=functools.cmp_to_key(compare_players), reverse=reverse)
        return [item["name"] for item in flat]


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
