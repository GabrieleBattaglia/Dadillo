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
            mn1, mn2, mres, mpts = data
            
            if mn1 == p1_name and mn2 == p2_name:
                if mres == '1': 
                    score_a += mpts
                    wins_a += 1
                elif mres == '2': 
                    score_b += mpts
                    wins_b += 1
                elif mres == '3':
                    score_a += mpts / 2.0
                    score_b += mpts / 2.0
            elif mn1 == p2_name and mn2 == p1_name:
                if mres == '1': 
                    score_b += mpts
                    wins_b += 1
                elif mres == '2': 
                    score_a += mpts
                    wins_a += 1
                elif mres == '3':
                    score_a += mpts / 2.0
                    score_b += mpts / 2.0
                    
        return score_a, score_b, wins_a, wins_b

    def update_display(self):
        order_by = self.cb_order.GetStringSelection()
        reverse = (self.cb_dir.GetSelection() == 0)
        
        # Prep player data
        # players: name -> [points, wins, draws, losses]
        flat = []
        for name, stats in self.tourney.players.items():
            flat.append({
                'name': name,
                'points': stats[0],
                'wins': stats[1],
                'draws': stats[2],
                'losses': stats[3]
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
                if isinstance(val_a, str): return (val_a > val_b) - (val_a < val_b)
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
            if days > 0: dur_str += f"{days} giorni, "
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
        lines.append(f"{'Pos':<5} | {'Giocatore':<20} | {'Punti':<8} | {'Vit':<5} | {'Par':<5} | {'Sco':<5} | Medaglia")
        lines.append("-" * 80)
        
        for idx, row in enumerate(flat):
            pos = idx + 1
            med_str = medals[idx] if idx < len(medals) else ""
            lines.append(f"{pos:<5} | {row['name']:<20} | {row['points']:<8.1f} | {row['wins']:<5} | {row['draws']:<5} | {row['losses']:<5} | {med_str}")
            
        lines.append("-" * 80)
        lines.append("")
        lines.append("RECORD DEL TORNEO")
        
        # Trova record ricalcolando
        recalto = ["Nessuno", "Nessuna", -99999]
        recbasso = ["Nessuno", "Nessuna", 99999]
        for m_id, data in self.tourney.played_matches.items():
            mn1, mn2, mres, mpts = data
            if mres == '1': winner = mn1
            elif mres == '2': winner = mn2
            else: winner = f"{mn1} (Pareggio) {mn2}"
            desc = f"({m_id}) {mn1} vs {mn2}"
            
            if mpts > recalto[2]:
                recalto = [winner, desc, mpts]
            if mpts < recbasso[2]:
                recbasso = [winner, desc, mpts]
                
        lines.append(f"Punteggio più alto: {recalto[0]} in {recalto[1]} con {recalto[2]} punti.")
        lines.append(f"Punteggio più basso: {recbasso[0]} in {recbasso[1]} con {recbasso[2]} punti.")
        
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
