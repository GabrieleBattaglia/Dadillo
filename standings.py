import wx
from datetime import datetime

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
        self.cb_order = wx.Choice(self, choices=["Punti", "Vittorie", "Sconfitte", "Pareggi", "Nome Giocatore"])
        
        # Imposta default in base ai setting
        if self.settings.main_criterion == "Vittorie":
            self.cb_order.SetStringSelection("Vittorie")
        else:
            self.cb_order.SetStringSelection("Punti")
            
        self.cb_order.Bind(wx.EVT_CHOICE, self.on_update)
        
        lbl_dir = wx.StaticText(self, label="Direzione:")
        self.cb_dir = wx.Choice(self, choices=["Discendente (Migliore in cima)", "Ascendente (Peggiore in cima)"])
        self.cb_dir.SetSelection(0)
        self.cb_dir.Bind(wx.EVT_CHOICE, self.on_update)
        
        ctrl_sizer.Add(lbl_order, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_order, 0, wx.ALL, 5)
        ctrl_sizer.Add(lbl_dir, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_dir, 0, wx.ALL, 5)
        
        main_sizer.Add(ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Text area
        self.txt_display = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        # Font a spaziatura fissa per allineare bene le colonne
        font = wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.txt_display.SetFont(font)
        
        main_sizer.Add(self.txt_display, 1, wx.EXPAND | wx.ALL, 10)
        
        # Aggiunta pulsanti DB o ritorno al torneo
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        if self.is_final:
            self.btn_db = wx.Button(self, label="Aggiorna DB giocatori")
            self.btn_db.Bind(wx.EVT_BUTTON, self.on_update_db)
            
            self.btn_db_all = wx.Button(self, label="Aggiorna tutti senza chiedere")
            self.btn_db_all.Bind(wx.EVT_BUTTON, self.on_update_db_all)
            
            btn_sizer.Add(self.btn_db, 0, wx.ALL, 5)
            btn_sizer.Add(self.btn_db_all, 0, wx.ALL, 5)
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
        self.update_display()
        
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
                if mres == '1':
                    pt1, pt2 = mpts, 0
                elif mres == '2':
                    pt1, pt2 = 0, mpts
                else:
                    pt1, pt2 = mpts / 2.0, mpts / 2.0
            
            if mn1 == p1_name and mn2 == p2_name:
                score_a += pt1
                score_b += pt2
                if mres == '1':
                    wins_a += 1
                elif mres == '2':
                    wins_b += 1
            elif mn1 == p2_name and mn2 == p1_name:
                score_b += pt1
                score_a += pt2
                if mres == '1':
                    wins_b += 1
                elif mres == '2':
                    wins_a += 1
                    
        return score_a, score_b, wins_a, wins_b
    def update_display(self):
        order_by = self.cb_order.GetStringSelection()
        reverse = (self.cb_dir.GetSelection() == 0)
        
        # Prep player data
        # players: name -> [points, wins, draws, losses]
        
        # Calcola le partite da giocare per ogni giocatore (per la colonna Giocate/Totale)
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
            
            flat.append({
                'name': name,
                'points': stats[0],
                'wins': stats[1],
                'draws': stats[2],
                'losses': stats[3],
                'played_str': played_str
            })
            
        import functools
        
        def compare_players(a, b):
            # 1. Criterio selezionato dall'utente sulla UI
            val_a = a['points']
            val_b = b['points']
            if order_by == "Vittorie":
                val_a, val_b = a['wins'], b['wins']
            elif order_by == "Sconfitte":
                val_a, val_b = a['losses'], b['losses']
            elif order_by == "Pareggi":
                val_a, val_b = a['draws'], b['draws']
            elif order_by == "Nome Giocatore":
                val_a, val_b = a['name'].lower(), b['name'].lower()
                
            if val_a != val_b:
                if isinstance(val_a, str):
                    return (val_a > val_b) - (val_a < val_b)
                return (val_a > val_b) - (val_a < val_b)
                
            # Se siamo qui, il criterio primario scelto a video è pari.
            # 2. Tiebreaker 1: Scontro Diretto
            if order_by != "Nome Giocatore":
                pts_a, pts_b, w_a, w_b = self._calculate_head_to_head(a['name'], b['name'])
                
                if "Punti" in self.settings.tiebreaker_1:
                    if pts_a != pts_b:
                        return (pts_a > pts_b) - (pts_a < pts_b)
                else: # Vittorie
                    if w_a != w_b:
                        return (w_a > w_b) - (w_a < w_b)
                        
            # 3. Tiebreaker 2: Globale
            if self.settings.tiebreaker_2 == "Punti Totali" and order_by != "Punti":
                if a['points'] != b['points']:
                    return (a['points'] > b['points']) - (a['points'] < b['points'])
            elif self.settings.tiebreaker_2 == "Vittorie Totali" and order_by != "Vittorie":
                if a['wins'] != b['wins']:
                    return (a['wins'] > b['wins']) - (a['wins'] < b['wins'])
                    
            # 4. Fallback: Ordine Alfabetico
            name_cmp = (a['name'] > b['name']) - (a['name'] < b['name'])
            if reverse:
                return -name_cmp # per l'alfabetico, se la lista è discendente (Z-A sui punti), vogliamo A-Z sui nomi
            return name_cmp

        flat.sort(key=functools.cmp_to_key(compare_players), reverse=reverse)
        
        # Costruzione del testo
        lines = []
        lines.append(f"Torneo: {self.tourney.title}")
        lines.append(f"Editto Divino: {self.tourney.comment}")
        lines.append("")
        
        start = self.tourney.start_date
        end = self.tourney.end_date if self.tourney.end_date else "In corso"
        lines.append(f"Data inizio: {start}")
        lines.append(f"Data fine: {end}")
        
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            dt_start = datetime.strptime(start, fmt)
            dt_end = datetime.strptime(self.tourney.end_date, fmt) if self.tourney.end_date else datetime.now()
            diff = dt_end - dt_start
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            days = diff.days
            dur_str = ""
            if days > 0:
                dur_str += f"{days} giorni, "
            dur_str += f"{hours} ore, {minutes} minuti."
            if not self.is_final:
                dur_str += " (Provvisoria)"
            lines.append(f"Durata complessiva: {dur_str}")
        except Exception:
            lines.append("Durata complessiva: Sconosciuta")
            
        lines.append("")
        lines.append("-" * 60)
        header_text = "CLASSIFICA FINALE" if self.is_final else "CLASSIFICA PARZIALE"
        lines.append(header_text)
        lines.append("-" * 60)
        
        medals = ["🥇 ORO", "🥈 ARGENTO", "🥉 BRONZO", "🪵 LEGNO (4° posto)"]
        
        # Intestazione colonne
        lines.append(f"{'Pos':<4} | {'Giocatore':<18} | {'Gio/Tot':<7} | {'Punti':<6} | {'Vit':<4} | {'Par':<4} | {'Sco':<4} | Medaglia")
        lines.append("-" * 85)
        
        for idx, row in enumerate(flat):
            pos = idx + 1
            med_str = medals[idx] if idx < len(medals) else ""
            
            # Formattazione punti senza .0 se intero
            p_val = row['points']
            if isinstance(p_val, (int, float)) and float(p_val).is_integer():
                p_str = str(int(p_val))
            else:
                p_str = f"{p_val:.1f}"
                
            lines.append(f"{pos:<4} | {row['name']:<18} | {row['played_str']:<7} | {p_str:<6} | {row['wins']:<4} | {row['draws']:<4} | {row['losses']:<4} | {med_str}")
            
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
            
            strikes = {name: 0 for name in self.tourney.players.keys()}
            current_strikes = {name: 0 for name in self.tourney.players.keys()}
            
            for m_id, data in self.tourney.played_matches.items():
                mn1, mn2, mres, mpts = data[:4]
                
                # Winner
                if mres == '1':
                    winner = mn1
                elif mres == '2':
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
                    
                # Strikes
                if mres == '1':
                    current_strikes[mn1] += 1
                    if current_strikes[mn1] > strikes[mn1]:
                        strikes[mn1] = current_strikes[mn1]
                    current_strikes[mn2] = 0
                elif mres == '2':
                    current_strikes[mn2] += 1
                    if current_strikes[mn2] > strikes[mn2]:
                        strikes[mn2] = current_strikes[mn2]
                    current_strikes[mn1] = 0
                else:
                    current_strikes[mn1] = 0
                    current_strikes[mn2] = 0

            def fmt_pts(p):
                return str(int(p)) if isinstance(p, (int, float)) and float(p).is_integer() else str(p)

            lines.append(f"Punteggio più alto: {fmt_pts(recalto_val)} punti.")
            for d in recalto_list:
                lines.append(f"  - {d}")
                
            lines.append(f"Punteggio più basso: {fmt_pts(recbasso_val)} punti.")
            for d in recbasso_list:
                lines.append(f"  - {d}")
                
            max_strike = max(strikes.values()) if strikes else 0
            if max_strike > 1:
                best_strikers = [p for p, v in strikes.items() if v == max_strike]
                lines.append(f"Striscia vincente più lunga: {max_strike} vittorie consecutive ({', '.join(best_strikers)})")

            max_draws = max([stats[2] for stats in self.tourney.players.values()]) if self.tourney.players else 0
            if max_draws > 0:
                best_drawers = [p for p, stats in self.tourney.players.items() if stats[2] == max_draws]
                lines.append(f"Re dei Pareggi: {max_draws} pareggi ({', '.join(best_drawers)})")

            import statistics
            all_pts = []
            sorted_items = sorted(self.tourney.played_matches.items(), key=lambda x: int(x[0]))
            for m_id, data in sorted_items:
                mpts = data[3]
                all_pts.append(float(mpts))
            
            if all_pts:
                lines.append("")
                mean_val = statistics.mean(all_pts)
                lines.append(f"Media aritmetica dei valori: {mean_val:.2f}")
                
                med_low = statistics.median_low(all_pts)
                med = statistics.median(all_pts)
                med_high = statistics.median_high(all_pts)
                lines.append(f"Mediane: bassa {med_low:+.2f}, media {med:+.2f}, alta {med_high:+.2f}.")
                
                try:
                    mode_val = statistics.mode(all_pts)
                    lines.append(f"Moda: {mode_val:+.2f}.")
                except statistics.StatisticsError:
                    pass
                
                if len(all_pts) > 1:
                    stdev_val = statistics.stdev(all_pts)
                    var_val = statistics.variance(all_pts)
                    lines.append(f"Deviazione standard: {stdev_val:+.2f}.")
                    lines.append(f"Varianza: {var_val:+.2f}.")
                
                tot_var = all_pts[-1] - all_pts[0]
                lines.append(f"Variazione totale dal primo all'ultimo record: {tot_var:+.2f}")
                
                if len(all_pts) > 1 and self.tourney.start_date:
                    try:
                        fmt = "%Y-%m-%d %H:%M:%S"
                        dt_start = datetime.strptime(self.tourney.start_date, fmt)
                        dt_end = datetime.strptime(self.tourney.end_date, fmt) if self.tourney.end_date else datetime.now()
                        diff = dt_end - dt_start
                        
                        freq_seconds = diff.total_seconds() / len(all_pts)
                        if freq_seconds > 0:
                            f_days, remainder = divmod(int(freq_seconds), 86400)
                            f_hours, remainder = divmod(remainder, 3600)
                            f_mins, f_secs = divmod(remainder, 60)
                            
                            parts = []
                            if f_days > 0: parts.append(f"{f_days} giorni")
                            if f_hours > 0: parts.append(f"{f_hours} ore")
                            if f_mins > 0: parts.append(f"{f_mins} minuti")
                            if f_secs > 0 or not parts: parts.append(f"{f_secs} secondi")
                            
                            lines.append(f"Ritmo medio di gioco: una partita ogni {', '.join(parts)}.")
                    except Exception:
                        pass
        
        self.txt_display.SetValue("\n".join(lines))
        self.current_standings = flat

    def on_back_to_tourney(self, event):
        self.GetParent().check_state_and_show()

    def on_update_db(self, event):
        self._process_db_update(ask_confirmation=True)

    def on_update_db_all(self, event):
        self._process_db_update(ask_confirmation=False)

    def _process_db_update(self, ask_confirmation):
        from data import PlayerDB
        db = PlayerDB()
        
        updates_done = 0
        
        for idx, row in enumerate(self.current_standings):
            name = row['name']
            pos = idx + 1
            is_oro = (pos == 1)
            is_argento = (pos == 2)
            is_bronzo = (pos == 3)
            is_legno = (pos == 4)
            
            do_update = True
            
            if name in db.players and ask_confirmation:
                ans = wx.MessageBox(f"Il formidabile {name} è già presente negli archivi sacri. Vuoi aggiornare il suo storico e il suo medagliere con il risultato di questo torneo (Posizione {pos})?", "Conferma Aggiornamento", wx.YES_NO | wx.ICON_QUESTION)
                if ans != wx.YES:
                    do_update = False
                    
            if do_update:
                start = self.tourney.start_date.split(" ")[0] if self.tourney.start_date else "Sconosciuta"
                end = self.tourney.end_date.split(" ")[0] if self.tourney.end_date else "Sconosciuta"
                
                db.add_or_update_player(name, pos, is_oro, is_argento, is_bronzo, is_legno, self.tourney.title, start, end)
                updates_done += 1
                
        if updates_done > 0:
            db.save()
            wx.MessageBox(f"Gli archivi sono stati aggiornati con {updates_done} registrazioni. Gloria eterna!", "Aggiornamento Completato")
        else:
            wx.MessageBox("Nessuna modifica apportata agli archivi.", "Operazione Annullata")
