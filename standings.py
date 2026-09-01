import contextlib

import wx
from data import (
    MAIN_CRITERIA,
    RANKING_VIEWS,
    TIEBREAKERS_1,
    TIEBREAKERS_2,
    format_date_extended,
    normalize_main_criterion,
    now_local,
    parse_timestamp,
)
from ui_utils import save_or_warn


def _extract_match_details(data):
    """Estrae (p1, p2, res, pt1, pt2) da un record partita, gestendo sia 4 che 6+ elementi."""
    if len(data) >= 6:
        mn1, mn2, mres, _, pt1, pt2 = data[:6]
    else:
        mn1, mn2, mres, mpts = data[:4]
        if mres == "1":
            pt1, pt2 = mpts, 0
        elif mres == "2":
            pt1, pt2 = 0, mpts
        else:
            pt1, pt2 = mpts / 2.0, mpts / 2.0
    return mn1, mn2, mres, pt1, pt2


def calculate_streaks(active_players, played_matches):
    """Striscia di vittorie consecutive piu' lunga di ogni giocatore.
    Le partite dei giocatori ritirati restano negli archivi del torneo anche
    dopo la loro rimozione dalla classifica: i contatori vanno quindi costruiti
    su tutti i nomi che compaiono nelle partite, altrimenti la schermata delle
    classifiche si interrompe con un errore. Il risultato riporta pero' solo i
    giocatori ancora in gara, che sono gli unici a comparire in classifica.
    """
    nomi = set(active_players)
    for data in played_matches.values():
        nomi.add(data[0])
        nomi.add(data[1])

    strikes = dict.fromkeys(nomi, 0)
    current = dict.fromkeys(nomi, 0)

    for data in played_matches.values():
        mn1, mn2, mres = data[0], data[1], data[2]
        if mres == "1":
            current[mn1] += 1
            strikes[mn1] = max(strikes[mn1], current[mn1])
            current[mn2] = 0
        elif mres == "2":
            current[mn2] += 1
            strikes[mn2] = max(strikes[mn2], current[mn2])
            current[mn1] = 0
        else:
            current[mn1] = 0
            current[mn2] = 0

    return {nome: valore for nome, valore in strikes.items() if nome in active_players}


def _calculate_mini_league_stats(group_names, played_matches):
    """Calcola punti e vittorie nel mini-girone per i soli giocatori del gruppo specificato."""
    mini_pts = {name: 0.0 for name in group_names}
    mini_wins = {name: 0 for name in group_names}

    for data in played_matches.values():
        mn1, mn2, mres, pt1, pt2 = _extract_match_details(data)
        if mn1 in group_names and mn2 in group_names:
            mini_pts[mn1] += pt1
            mini_pts[mn2] += pt2
            if mres == "1":
                mini_wins[mn1] += 1
            elif mres == "2":
                mini_wins[mn2] += 1

    return mini_pts, mini_wins


def rank_tournament_players(
    players_dict,
    played_matches,
    order_by="Vittorie",
    score_direction="Alto",
    tiebreaker_1="Scontro Diretto (Punti)",
    tiebreaker_2="Punti Totali",
    unplayed_matches=None,
    reverse=True,
):
    """
    Ordina i giocatori di un torneo con il metodo a gruppi e sottogruppi ricorsivi (classifica avulsa).
    Risolve correttamente le parità a 2, 3 o più giocatori secondo le regole impostate.
    """
    unplayed_counts = {name: 0 for name in players_dict}
    if unplayed_matches:
        for p1, p2 in unplayed_matches.values():
            if p1 in unplayed_counts:
                unplayed_counts[p1] += 1
            if p2 in unplayed_counts:
                unplayed_counts[p2] += 1

    all_players = []
    for name, stats in players_dict.items():
        played = stats[1] + stats[2] + stats[3]
        total = played + unplayed_counts.get(name, 0)
        played_str = f"{played}/{total}"
        all_players.append(
            {
                "name": name,
                "points": stats[0],
                "wins": stats[1],
                "draws": stats[2],
                "losses": stats[3],
                "played_str": played_str,
            }
        )

    if not all_players:
        return []

    is_points_order = order_by.startswith("Punti")

    def _resolve_subgroup(sub, current_tie_stage):
        if len(sub) <= 1:
            return sub

        if current_tie_stage == "tie1":
            if tiebreaker_1 != "Nessuno":
                sub_names = {p["name"] for p in sub}
                mini_pts, mini_wins = _calculate_mini_league_stats(
                    sub_names, played_matches
                )

                mini_subgroups = {}
                for p in sub:
                    name = p["name"]
                    if "Punti" in tiebreaker_1:
                        sc = mini_pts[name]
                    elif "Vittorie" in tiebreaker_1:
                        sc = mini_wins[name]
                    else:
                        sc = 0
                    mini_subgroups.setdefault(sc, []).append(p)

                if "Punti" in tiebreaker_1 and score_direction == "Basso":
                    sorted_scores = sorted(mini_subgroups.keys())
                else:
                    sorted_scores = sorted(mini_subgroups.keys(), reverse=True)

                if len(sorted_scores) > 1:
                    res = []
                    for sc in sorted_scores:
                        smaller_group = mini_subgroups[sc]
                        if len(smaller_group) == 1:
                            res.extend(smaller_group)
                        else:
                            res.extend(
                                _resolve_subgroup(
                                    smaller_group, current_tie_stage="tie1"
                                )
                            )
                    return res
                else:
                    return _resolve_subgroup(sub, current_tie_stage="tie2")
            else:
                return _resolve_subgroup(sub, current_tie_stage="tie2")

        elif current_tie_stage == "tie2":
            if tiebreaker_2 != "Nessuno":
                tie2_scores = {}
                for p in sub:
                    if tiebreaker_2 == "Punti Totali" and not is_points_order:
                        tie2_scores[p["name"]] = p["points"]
                    elif tiebreaker_2 == "Vittorie Totali" and order_by != "Vittorie":
                        tie2_scores[p["name"]] = p["wins"]
                    else:
                        tie2_scores[p["name"]] = 0

                tie2_subgroups = {}
                for p in sub:
                    sc = tie2_scores[p["name"]]
                    tie2_subgroups.setdefault(sc, []).append(p)

                if (
                    tiebreaker_2 == "Punti Totali"
                    and not is_points_order
                    and score_direction == "Basso"
                ):
                    sorted_scores = sorted(tie2_subgroups.keys())
                else:
                    sorted_scores = sorted(tie2_subgroups.keys(), reverse=True)

                if len(sorted_scores) > 1:
                    res = []
                    for sc in sorted_scores:
                        smaller_group = tie2_subgroups[sc]
                        if len(smaller_group) == 1:
                            res.extend(smaller_group)
                        else:
                            res.extend(
                                _resolve_subgroup(
                                    smaller_group, current_tie_stage="tie1"
                                )
                            )
                    return res
                else:
                    return _resolve_subgroup(sub, current_tie_stage="fallback")
            else:
                return _resolve_subgroup(sub, current_tie_stage="fallback")

        else:
            return sorted(sub, key=lambda p: p["name"].lower())

    # Raggruppamento per Criterio Principale
    main_subgroups = {}
    for p in all_players:
        if order_by == "Vittorie":
            key = p["wins"]
        elif is_points_order:
            key = p["points"]
        elif order_by == "Sconfitte":
            key = p["losses"]
        elif order_by == "Pareggi":
            key = p["draws"]
        elif order_by.startswith("Nome"):
            key = p["name"].lower()
        else:
            key = p["wins"]
        main_subgroups.setdefault(key, []).append(p)

    if order_by == "Vittorie" or order_by == "Pareggi":
        sorted_main_keys = sorted(main_subgroups.keys(), reverse=True)
    elif is_points_order:
        sorted_main_keys = (
            sorted(main_subgroups.keys())
            if score_direction == "Basso"
            else sorted(main_subgroups.keys(), reverse=True)
        )
    elif order_by == "Sconfitte" or order_by.startswith("Nome"):
        sorted_main_keys = sorted(main_subgroups.keys())
    else:
        sorted_main_keys = sorted(main_subgroups.keys(), reverse=True)

    ranked_best_to_worst = []
    for key in sorted_main_keys:
        sub = main_subgroups[key]
        if len(sub) == 1 or order_by.startswith("Nome"):
            ranked_best_to_worst.extend(sub)
        else:
            ranked_best_to_worst.extend(
                _resolve_subgroup(sub, current_tie_stage="tie1")
            )

    if not reverse:
        return list(reversed(ranked_best_to_worst))
    return ranked_best_to_worst


class StandingsPanel(wx.Panel):
    def __init__(self, parent, tourney, settings, is_final=True):
        super().__init__(parent)
        self.tourney = tourney
        self.settings = settings
        self.is_final = is_final

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Controls on top
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl_order = wx.StaticText(self, label="Ordina per:")
        self.cb_order = wx.Choice(self, choices=list(RANKING_VIEWS))

        main_crit = getattr(
            self.tourney,
            "main_criterion",
            getattr(self.settings, "main_criterion", MAIN_CRITERIA[0]),
        )
        # normalize_main_criterion riconosce anche le vecchie etichette, per
        # esempio Punti Totali, che altrimenti facevano ricadere l'ordinamento
        # su Vittorie senza dirlo a nessuno.
        self.cb_order.SetStringSelection(normalize_main_criterion(main_crit))

        self.cb_order.Bind(wx.EVT_CHOICE, self.on_update)

        lbl_score_dir = wx.StaticText(self, label="Priorità Punteggio:")
        self.cb_score_dir = wx.Choice(
            self,
            choices=["Punteggio più alto (Migliore)", "Punteggio più basso (Migliore)"],
        )
        score_dir = getattr(
            self.tourney,
            "score_direction",
            getattr(self.settings, "score_direction", "Alto"),
        )
        if score_dir == "Basso":
            self.cb_score_dir.SetSelection(1)
        else:
            self.cb_score_dir.SetSelection(0)
        self.cb_score_dir.Bind(wx.EVT_CHOICE, self.on_update)

        lbl_tie1 = wx.StaticText(self, label="1° Spareggio:")
        self.cb_tie1 = wx.Choice(self, choices=list(TIEBREAKERS_1))
        tie1 = getattr(
            self.tourney,
            "tiebreaker_1",
            getattr(self.settings, "tiebreaker_1", TIEBREAKERS_1[0]),
        )
        if tie1 in TIEBREAKERS_1:
            self.cb_tie1.SetStringSelection(tie1)
        else:
            self.cb_tie1.SetSelection(0)
        self.cb_tie1.Bind(wx.EVT_CHOICE, self.on_update)

        lbl_tie2 = wx.StaticText(self, label="2° Spareggio:")
        self.cb_tie2 = wx.Choice(self, choices=list(TIEBREAKERS_2))
        tie2 = getattr(
            self.tourney,
            "tiebreaker_2",
            getattr(self.settings, "tiebreaker_2", TIEBREAKERS_2[0]),
        )
        if tie2 in TIEBREAKERS_2:
            self.cb_tie2.SetStringSelection(tie2)
        else:
            self.cb_tie2.SetSelection(0)
        self.cb_tie2.Bind(wx.EVT_CHOICE, self.on_update)

        lbl_dir = wx.StaticText(self, label="Direzione:")
        self.cb_dir = wx.Choice(
            self,
            choices=["Discendente (Migliore in cima)", "Ascendente (Peggiore in cima)"],
        )
        self.cb_dir.SetSelection(0)
        self.cb_dir.Bind(wx.EVT_CHOICE, self.on_update)

        ctrl_sizer.Add(lbl_order, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_order, 0, wx.ALL, 5)
        ctrl_sizer.Add(lbl_score_dir, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_score_dir, 0, wx.ALL, 5)
        ctrl_sizer.Add(lbl_tie1, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_tie1, 0, wx.ALL, 5)
        ctrl_sizer.Add(lbl_tie2, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_tie2, 0, wx.ALL, 5)
        ctrl_sizer.Add(lbl_dir, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_dir, 0, wx.ALL, 5)

        main_sizer.Add(ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Text area
        self.txt_display = wx.TextCtrl(
            self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )
        # Font a spaziatura fissa per allineare bene le colonne
        font = wx.Font(
            11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        self.txt_display.SetFont(font)

        main_sizer.Add(self.txt_display, 1, wx.EXPAND | wx.ALL, 10)

        # Aggiunta pulsanti DB o ritorno al torneo
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.is_final:
            self.btn_proceed = wx.Button(
                self, label="Avanti: Conferma Criteri e Assegna Medaglie"
            )
            self.btn_proceed.Bind(wx.EVT_BUTTON, self.on_proceed)
            btn_sizer.Add(self.btn_proceed, 0, wx.ALL, 5)
        else:
            self.btn_back = wx.Button(self, label="Torna alle Partite")
            self.btn_back.Bind(wx.EVT_BUTTON, self.on_back_to_tourney)
            btn_sizer.Add(self.btn_back, 0, wx.ALL, 5)

        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizer(main_sizer)
        self.update_display()

        # Forza il focus per lo screen reader
        wx.CallAfter(self.txt_display.SetFocus)

    def on_update(self, event):
        order_sel = self.cb_order.GetStringSelection()
        if order_sel in ["Vittorie", "Punti"]:
            self.tourney.main_criterion = order_sel

        score_dir_idx = self.cb_score_dir.GetSelection()
        self.tourney.score_direction = "Alto" if score_dir_idx == 0 else "Basso"

        self.tourney.tiebreaker_1 = self.cb_tie1.GetStringSelection()
        self.tourney.tiebreaker_2 = self.cb_tie2.GetStringSelection()

        save_or_warn(self.tourney.save, self)
        self.update_display()

    def update_display(self):
        order_by = self.cb_order.GetStringSelection()
        score_direction = "Alto" if self.cb_score_dir.GetSelection() == 0 else "Basso"
        tiebreaker_1 = self.cb_tie1.GetStringSelection()
        tiebreaker_2 = self.cb_tie2.GetStringSelection()
        reverse = self.cb_dir.GetSelection() == 0

        flat = rank_tournament_players(
            self.tourney.players,
            self.tourney.played_matches,
            order_by=order_by,
            score_direction=score_direction,
            tiebreaker_1=tiebreaker_1,
            tiebreaker_2=tiebreaker_2,
            unplayed_matches=self.tourney.unplayed_matches,
            reverse=reverse,
        )
        lines = []
        lines.append(f"Torneo: {self.tourney.title}")
        lines.append(f"Editto Divino: {self.tourney.comment}")
        lines.append("")

        start = self.tourney.start_date
        end = self.tourney.end_date if self.tourney.end_date else "In corso"
        formatted_start = format_date_extended(start) if start else "Sconosciuta"
        formatted_end = (
            format_date_extended(end) if self.tourney.end_date else "In corso"
        )
        lines.append(f"Data inizio: {formatted_start}")
        lines.append(f"Data fine: {formatted_end}")

        # Le due estremita' vanno confrontate nello stesso fuso orario, altrimenti
        # la durata sbaglia di tutto l'offset e per i tornei appena iniziati
        # risulta addirittura negativa.
        dt_start = parse_timestamp(start)
        dt_end = (
            parse_timestamp(self.tourney.end_date)
            if self.tourney.end_date
            else now_local()
        )
        if dt_start is None or dt_end is None:
            lines.append("Durata complessiva: Sconosciuta")
        else:
            diff = dt_end - dt_start
            secondi_totali = max(int(diff.total_seconds()), 0)
            days, resto = divmod(secondi_totali, 86400)
            hours, resto = divmod(resto, 3600)
            minutes = resto // 60
            dur_str = ""
            if days > 0:
                dur_str += f"{days} giorni, "
            dur_str += f"{hours} ore, {minutes} minuti."
            if not self.is_final:
                dur_str += " (Provvisoria)"
            lines.append(f"Durata complessiva: {dur_str}")

        lines.append("")
        lines.append("-" * 60)
        header_text = "CLASSIFICA FINALE" if self.is_final else "CLASSIFICA PARZIALE"
        lines.append(header_text)
        lines.append("-" * 60)

        medals = ["🥇 ORO", "🥈 ARGENTO", "🥉 BRONZO", "🪵 LEGNO (4° posto)"]

        # Intestazione colonne
        lines.append(
            f"{'Pos':<4} | {'Giocatore':<18} | {'Gio/Tot':<7} | {'Punti':<6} | {'Vit':<4} | {'Par':<4} | {'Sco':<4} | Medaglia"
        )
        lines.append("-" * 85)

        for idx, row in enumerate(flat):
            if reverse:
                pos = idx + 1
            else:
                pos = len(flat) - idx

            med_str = medals[pos - 1] if (pos - 1) < len(medals) else ""

            # Formattazione punti senza .0 se intero
            p_val = row["points"]
            if isinstance(p_val, (int, float)) and float(p_val).is_integer():
                p_str = str(int(p_val))
            else:
                p_str = f"{p_val:.1f}"

            lines.append(
                f"{pos:<4} | {row['name']:<18} | {row['played_str']:<7} | {p_str:<6} | {row['wins']:<4} | {row['draws']:<4} | {row['losses']:<4} | {med_str}"
            )

        lines.append("-" * 85)
        lines.append("")
        lines.append("STATISTICHE E RECORD")

        if not self.tourney.played_matches:
            lines.append("Nessuna partita ancora giocata.")
        else:
            recalto_val = -99999
            recbasso_val = 99999
            recalto_list = []
            recbasso_list = []

            strikes = calculate_streaks(
                self.tourney.players, self.tourney.played_matches
            )

            for m_id, data in self.tourney.played_matches.items():
                mn1, mn2, mres, mpts = data[:4]

                # Winner
                if mres == "1":
                    winner = mn1
                elif mres == "2":
                    winner = mn2
                else:
                    winner = f"{mn1} (Pareggio) {mn2}"
                desc = f"{winner} in ({m_id}) {mn1} vs {mn2}"

                if mpts > recalto_val:
                    recalto_val = mpts
                    recalto_list = [desc]
                elif mpts == recalto_val:
                    recalto_list.append(desc)

                if mpts < recbasso_val:
                    recbasso_val = mpts
                    recbasso_list = [desc]
                elif mpts == recbasso_val:
                    recbasso_list.append(desc)

            def fmt_pts(p):
                return (
                    str(int(p))
                    if isinstance(p, (int, float)) and float(p).is_integer()
                    else str(p)
                )

            lines.append(f"Punteggio più alto: {fmt_pts(recalto_val)} punti.")
            for d in recalto_list:
                lines.append(f"  - {d}")

            lines.append(f"Punteggio più basso: {fmt_pts(recbasso_val)} punti.")
            for d in recbasso_list:
                lines.append(f"  - {d}")

            max_strike = max(strikes.values()) if strikes else 0
            if max_strike > 1:
                best_strikers = [p for p, v in strikes.items() if v == max_strike]
                lines.append(
                    f"Striscia vincente più lunga: {max_strike} vittorie consecutive ({', '.join(best_strikers)})"
                )

            max_draws = (
                max([stats[2] for stats in self.tourney.players.values()])
                if self.tourney.players
                else 0
            )
            if max_draws > 0:
                best_drawers = [
                    p
                    for p, stats in self.tourney.players.items()
                    if stats[2] == max_draws
                ]
                lines.append(
                    f"Re dei Pareggi: {max_draws} pareggi ({', '.join(best_drawers)})"
                )

            import statistics

            all_pts = []
            win_pts = []
            draw_pts = []

            sorted_items = sorted(
                self.tourney.played_matches.items(), key=lambda x: int(x[0])
            )
            for m_id, data in sorted_items:
                mres = data[2]
                mpts = data[3]
                val = float(mpts)
                all_pts.append(val)

                if mres in ("1", "2"):
                    win_pts.append(val)
                elif mres == "3":
                    # Il codice del pareggio e' 3 in tutto il programma: il
                    # confronto con X non era mai vero e la media dei pareggi
                    # non veniva mai calcolata.
                    draw_pts.append(val)

            if all_pts:
                lines.append("")
                lines.append("ALTRE STATISTICHE SUI PUNTEGGI ASSEGNATI")

                somma_totale = sum(all_pts)
                lines.append(
                    f"Somma totale dei punti assegnati: {fmt_pts(somma_totale)}"
                )

                mean_val = statistics.mean(all_pts)
                lines.append(f"Media aritmetica globale: {mean_val:.2f}")

                if win_pts:
                    mean_win = statistics.mean(win_pts)
                    lines.append(f"  - Media punti per partita vinta: {mean_win:.2f}")
                if draw_pts:
                    mean_draw = statistics.mean(draw_pts)
                    lines.append(f"  - Media punti per pareggio: {mean_draw:.2f}")

                med_low = statistics.median_low(all_pts)
                med = statistics.median(all_pts)
                med_high = statistics.median_high(all_pts)
                lines.append(
                    f"Mediane: bassa {med_low:+.2f}, media {med:+.2f}, alta {med_high:+.2f}."
                )

                try:
                    mode_val = statistics.mode(all_pts)
                    lines.append(f"Moda: {mode_val:+.2f}.")
                except statistics.StatisticsError:
                    pass

                if len(all_pts) >= 4:
                    with contextlib.suppress(
                        ValueError, TypeError, ZeroDivisionError, IndexError
                    ):
                        sorted_pts = sorted(all_pts)
                        min_val = sorted_pts[0]
                        max_val = sorted_pts[-1]

                        if max_val > min_val:
                            # Suddivisione in 4 fasce in base all'escursione dei punteggi
                            step = (max_val - min_val) / 4.0

                            fasce_data = []
                            for i in range(4):
                                fascia_min = min_val + (i * step)
                                # L'ultima fascia include anche il valore massimo esatto
                                if i == 3:
                                    fascia_max = max_val
                                    pts_in_fascia = [
                                        p
                                        for p in sorted_pts
                                        if p >= fascia_min and p <= fascia_max
                                    ]
                                else:
                                    fascia_max = min_val + ((i + 1) * step)
                                    pts_in_fascia = [
                                        p
                                        for p in sorted_pts
                                        if p >= fascia_min and p < fascia_max
                                    ]

                                count = len(pts_in_fascia)
                                q_mean = sum(pts_in_fascia) / count if count > 0 else 0

                                fasce_data.append(
                                    {
                                        "name": f"Fascia {i + 1}",
                                        "count": count,
                                        "min": fascia_min,
                                        "max": fascia_max,
                                        "mean": q_mean,
                                    }
                                )

                            if fasce_data:
                                lines.append("")
                                lines.append(
                                    "SUDDIVISIONE PER FASCE DI PUNTEGGIO (Dal peggiore al migliore):"
                                )
                                for q in fasce_data:
                                    if q["count"] > 0:
                                        lines.append(
                                            f"  {q['name']}: {q['count']} partite - Punteggi da {fmt_pts(q['min'])} a {fmt_pts(q['max'])} (Media: {q['mean']:.2f})"
                                        )
                                    else:
                                        lines.append(
                                            f"  {q['name']}: 0 partite - Punteggi da {fmt_pts(q['min'])} a {fmt_pts(q['max'])}"
                                        )
                elif len(all_pts) > 1:
                    with contextlib.suppress(AttributeError, ValueError):
                        # Fallback alla visualizzazione base se ci sono meno di 4 partite (non si possono fare 4 gruppi reali)
                        quartiles = statistics.quantiles(all_pts, n=4)
                        q1 = quartiles[0]
                        q3 = quartiles[2]
                        lines.append(
                            f"Quartili: il 25% dei punteggi registrati è inferiore a {q1:.2f} punti; il 25% è superiore a {q3:.2f} punti."
                        )

                if len(all_pts) > 1:
                    stdev_val = statistics.stdev(all_pts)
                    var_val = statistics.variance(all_pts)
                    lines.append(f"Deviazione standard: {stdev_val:+.2f}.")
                    lines.append(f"Varianza: {var_val:+.2f}.")

                    if mean_val != 0:
                        cv = (stdev_val / mean_val) * 100
                        lines.append(f"Coefficiente di variazione: {cv:.2f}%")

                range_val = max(all_pts) - min(all_pts)
                lines.append(
                    f"Escursione (forbice tra il valore più alto e il più basso): {range_val:+.2f}"
                )

                if len(all_pts) > 1 and self.tourney.start_date:
                    ritmo_start = parse_timestamp(self.tourney.start_date)
                    ritmo_end = (
                        parse_timestamp(self.tourney.end_date)
                        if self.tourney.end_date
                        else now_local()
                    )
                    if ritmo_start is not None and ritmo_end is not None:
                        diff = ritmo_end - ritmo_start

                        freq_seconds = max(diff.total_seconds(), 0) / len(all_pts)
                        if freq_seconds > 0:
                            f_days, remainder = divmod(int(freq_seconds), 86400)
                            f_hours, remainder = divmod(remainder, 3600)
                            f_mins, f_secs = divmod(remainder, 60)

                            parts = []
                            if f_days > 0:
                                parts.append(f"{f_days} giorni")
                            if f_hours > 0:
                                parts.append(f"{f_hours} ore")
                            if f_mins > 0:
                                parts.append(f"{f_mins} minuti")
                            if f_secs > 0 or not parts:
                                parts.append(f"{f_secs} secondi")

                            lines.append(
                                f"Ritmo medio di gioco: una partita ogni {', '.join(parts)}."
                            )

        self.txt_display.SetValue("\n".join(lines))
        self.current_standings = flat

    def on_back_to_tourney(self, event):
        self.GetParent().init_main_ui()

    def on_proceed(self, event):
        from data import PlayerDB
        from dialogs import (
            SinglePlayerReviewDialog,
            TournamentFinalReviewChoiceDialog,
        )

        order_by = self.cb_order.GetStringSelection()
        score_direction = "Alto" if self.cb_score_dir.GetSelection() == 0 else "Basso"
        tiebreaker_1 = self.cb_tie1.GetStringSelection()
        tiebreaker_2 = self.cb_tie2.GetStringSelection()

        # Salva le scelte definitive nel file del torneo
        if order_by in ["Vittorie", "Punti"]:
            self.tourney.main_criterion = order_by
        self.tourney.score_direction = score_direction
        self.tourney.tiebreaker_1 = tiebreaker_1
        self.tourney.tiebreaker_2 = tiebreaker_2
        save_or_warn(self.tourney.save, self)

        # Calcola la classifica ufficiale (sempre 1° posto al migliore, indipendentemente dalla vista temporanea)
        official_standings = rank_tournament_players(
            self.tourney.players,
            self.tourney.played_matches,
            order_by=order_by,
            score_direction=score_direction,
            tiebreaker_1=tiebreaker_1,
            tiebreaker_2=tiebreaker_2,
            unplayed_matches=self.tourney.unplayed_matches,
            reverse=True,
        )

        choice_dlg = TournamentFinalReviewChoiceDialog(self)
        choice_dlg.ShowModal()
        choice = choice_dlg.choice
        choice_dlg.Destroy()

        db = PlayerDB()
        updates_done = 0
        skipped_count = 0

        medals_map = {1: "🥇 ORO", 2: "🥈 ARGENTO", 3: "🥉 BRONZO", 4: "🪵 LEGNO"}

        start = (
            format_date_extended(self.tourney.start_date)
            if self.tourney.start_date
            else "Sconosciuta"
        )
        end = (
            format_date_extended(self.tourney.end_date)
            if self.tourney.end_date
            else "Sconosciuta"
        )

        for idx, row in enumerate(official_standings):
            name = row["name"]
            pos = idx + 1
            is_oro = pos == 1
            is_argento = pos == 2
            is_bronzo = pos == 3
            is_legno = pos == 4
            med_str = medals_map.get(pos, "")

            do_update = True
            if choice == "individual":
                rev_dlg = SinglePlayerReviewDialog(
                    self,
                    player_name=name,
                    position=pos,
                    medal_str=med_str,
                    tourney_title=self.tourney.title,
                    start_date=start,
                    end_date=end,
                )
                res = rev_dlg.ShowModal()
                rev_dlg.Destroy()
                if res != wx.ID_OK:
                    do_update = False
                    skipped_count += 1

            if do_update:
                success = db.add_or_update_player(
                    name,
                    pos,
                    is_oro,
                    is_argento,
                    is_bronzo,
                    is_legno,
                    self.tourney.title,
                    start,
                    end,
                )
                if success:
                    updates_done += 1
                else:
                    skipped_count += 1

        if not save_or_warn(db.save, self):
            wx.MessageBox(
                "Le medaglie non sono state\n"
                "registrate: l'archivio dei\n"
                "discepoli non e' stato salvato.\n"
                "Risolvi il problema e premi di\n"
                "nuovo il pulsante Avanti.",
                "Premiazione non registrata",
                wx.OK | wx.ICON_ERROR,
            )
            return

        msg = (
            "Oh mio insuperabile e implacabile dominatore!\n\n"
            "I verdetti ufficiali sono stati incisi nella pietra digitale della Hall of Fame:\n"
            f"• Discepoli aggiornati con successo: {updates_done}\n"
        )
        if skipped_count > 0:
            msg += f"• Discepoli saltati o tornei già registrati: {skipped_count}\n"

        msg += (
            "\nIl file testuale 'Giocatori.txt' è stato aggiornato all'istante.\n"
            "Gloria eterna!"
        )

        wx.MessageBox(
            msg, "Premiazione e Registrazione Conclusa", wx.OK | wx.ICON_INFORMATION
        )

        if hasattr(self, "btn_proceed"):
            self.btn_proceed.Disable()
            self.btn_proceed.SetLabel("Medaglie e Storico già Assegnati")
