import wx

class SetupTournamentDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Nuovo Torneo di Adorazione", size=(550, 500))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        msg = wx.StaticText(panel, label="Oh mio adorato, supremo Maestro!\nDimmi come vuoi chiamare questo nuovo atto di sottomissione:")
        vbox.Add(msg, 0, wx.ALL | wx.EXPAND, 10)
        
        lbl_title = wx.StaticText(panel, label="Nome Torneo:")
        self.txt_title = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.txt_title.Bind(wx.EVT_TEXT_ENTER, self.on_title_enter)
        vbox.Add(lbl_title, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.txt_title, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        lbl_comment = wx.StaticText(panel, label="Commento / Editto divino:")
        self.txt_comment = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.txt_comment.Bind(wx.EVT_KEY_DOWN, self.on_comment_key)
        vbox.Add(lbl_comment, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.txt_comment, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        # --- NEW SETTINGS FOR V2.1.0 ---
        # 1. Tipologia di girone
        lbl_type = wx.StaticText(panel, label="Tipologia di Girone:")
        self.cb_type = wx.Choice(panel, choices=["Girone all'Italiana (Andata e Ritorno)", "Girone all'Italiana (Solo Andata)"])
        self.cb_type.SetSelection(0) # Default: Andata e Ritorno
        vbox.Add(lbl_type, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_type, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        # 2. Punteggi Predefiniti
        pts_box = wx.StaticBoxSizer(wx.StaticBox(panel, label="Punteggi Predefiniti (Lascia vuoto per chiedere ogni volta)"), wx.HORIZONTAL)
        
        lbl_win = wx.StaticText(panel, label=" Vittoria:")
        self.txt_win = wx.TextCtrl(panel, size=(50, -1))
        
        lbl_draw = wx.StaticText(panel, label=" Pareggio:")
        self.txt_draw = wx.TextCtrl(panel, size=(50, -1))
        
        lbl_loss = wx.StaticText(panel, label=" Sconfitta:")
        self.txt_loss = wx.TextCtrl(panel, size=(50, -1))
        
        pts_box.Add(lbl_win, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        pts_box.Add(self.txt_win, 0, wx.ALL, 5)
        pts_box.Add(lbl_draw, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        pts_box.Add(self.txt_draw, 0, wx.ALL, 5)
        pts_box.Add(lbl_loss, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        pts_box.Add(self.txt_loss, 0, wx.ALL, 5)
        
        vbox.Add(pts_box, 0, wx.LEFT | wx.RIGHT | wx.EXPAND | wx.TOP, 10)
        # -------------------------------
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, "Sia fatta la tua volontà!")
        self.btn_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Pietà, ho cambiato idea!")
        btn_box.Add(self.btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(vbox)
        
    def on_title_enter(self, event):
        self.txt_comment.SetFocus()

    def on_comment_key(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN and not event.ShiftDown():
            # Se premi invio senza shift nel multiline, salta al successivo
            self.cb_type.SetFocus()
        else:
            event.Skip()

    def on_ok(self, event):
        # Valida i punteggi se non sono vuoti
        for txt, nome in [(self.txt_win, "Vittoria"), (self.txt_draw, "Pareggio"), (self.txt_loss, "Sconfitta")]:
            val = txt.GetValue().strip()
            if val:
                try:
                    float(val)
                except ValueError:
                    wx.MessageBox(f"Oh fonte di inesauribile calcolo, il punteggio per la {nome} non sembra un numero valido. Puoi perdonare la mia stoltezza e correggerlo?", "Errore di conversione", wx.OK | wx.ICON_ERROR)
                    txt.SetFocus()
                    return
        event.Skip()

    def get_data(self):
        title = self.txt_title.GetValue().strip()
        comment = self.txt_comment.GetValue().strip()
        tourney_type = self.cb_type.GetSelection()
        
        def parse_pts(txt):
            val = txt.GetValue().strip()
            return float(val) if val else None
            
        pts_win = parse_pts(self.txt_win)
        pts_draw = parse_pts(self.txt_draw)
        pts_loss = parse_pts(self.txt_loss)
        
        return title, comment, tourney_type, pts_win, pts_draw, pts_loss


class SetupPlayersDialog(wx.Dialog):
    def __init__(self, parent, existing_players=None):
        super().__init__(parent, title="Raduna i Tuoi Discepoli", size=(500, 650))

        self.players = existing_players[:] if existing_players else []

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg = wx.StaticText(panel, label="Mia estremitudine immortale, inserisci i nomi dei tuoi seguaci.")
        vbox.Add(msg, 0, wx.ALL | wx.EXPAND, 10)

        # Listbox per i giocatori del DB
        from data import PlayerDB
        db = PlayerDB()
        db_players = sorted(list(db.players.keys()))

        lbl_db = wx.StaticText(panel, label="Seleziona dal database (Spazio o Doppio Clic per aggiungere):")
        self.list_db_players = wx.ListBox(panel, choices=db_players, style=wx.LB_SINGLE, size=(-1, 120))
        self.list_db_players.Bind(wx.EVT_KEY_DOWN, self.on_db_key_down)
        self.list_db_players.Bind(wx.EVT_LISTBOX_DCLICK, self.on_db_dclick)

        vbox.Add(lbl_db, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.list_db_players, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        self.lbl_player = wx.StaticText(panel, label=f"Giocatore {len(self.players) + 1}:")
        self.txt_player = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.txt_player.Bind(wx.EVT_TEXT_ENTER, self.on_add_player)

        vbox.Add(self.lbl_player, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.txt_player, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        lbl_list = wx.StaticText(panel, label="Lista Discepoli partecipanti (Premi Canc per sopprimere l'eretico):")
        self.list_players = wx.ListBox(panel, style=wx.LB_SORT | wx.LB_SINGLE)
        self.list_players.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        for p in self.players:
            self.list_players.Append(p)

        vbox.Add(lbl_list, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.list_players, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK, "Tutti pronti al massacro!")
        btn_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        btn_wait = wx.Button(panel, wx.ID_APPLY, "Resta in attesa...")
        btn_wait.Bind(wx.EVT_BUTTON, self.on_wait)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Annulla tutto, mio sole!")

        btn_box.Add(btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_wait, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)

        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(vbox)

    def on_db_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            sel = self.list_db_players.GetSelection()
            if sel != wx.NOT_FOUND:
                name = self.list_db_players.GetString(sel)
                self.add_from_db(name)
        else:
            event.Skip()

    def on_db_dclick(self, event):
        sel = self.list_db_players.GetSelection()
        if sel != wx.NOT_FOUND:
            name = self.list_db_players.GetString(sel)
            self.add_from_db(name)

    def add_from_db(self, name):
        if name in self.players:
            wx.MessageBox(f"Mi scudiscio per la vergogna, ma {name} è già presente nel torneo.", "Giocatore già aggiunto", wx.OK | wx.ICON_WARNING)
            return
        self.players.append(name)
        self.list_players.Append(name)
        self.lbl_player.SetLabel(f"Giocatore {len(self.players) + 1}:")
        wx.CallLater(300, self.list_players.SetFocus)

    def on_add_player(self, event):
        name = self.txt_player.GetValue().strip()
        if not name:
            return
        if len(name) < 3:
            wx.MessageBox("Oh insondabile pozzo di saggezza, un nome di sole 2 lettere è un insulto alla tua grandezza! Servono almeno 3 caratteri.", "Nome troppo corto", wx.OK | wx.ICON_WARNING)
            self.txt_player.SelectAll()
            return
        if name in self.players:
            wx.MessageBox(f"Mi scudiscio per la vergogna, ma {name} l'abbiamo già convertito al nostro volere.", "Nome duplicato", wx.OK | wx.ICON_WARNING)
            self.txt_player.SelectAll()
            return
            
        self.players.append(name)
        self.list_players.Append(name)
        self.txt_player.SetValue("")
        self.lbl_player.SetLabel(f"Giocatore {len(self.players) + 1}:")
        
        wx.CallLater(300, self.list_players.SetFocus)
        wx.CallLater(600, self.txt_player.SetFocus)
        
    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            sel = self.list_players.GetSelection()
            if sel != wx.NOT_FOUND:
                name = self.list_players.GetString(sel)
                self.players.remove(name)
                self.list_players.Delete(sel)
                self.lbl_player.SetLabel(f"Giocatore {len(self.players) + 1}:")
                wx.CallLater(300, self.list_players.SetFocus)
                wx.CallLater(600, self.txt_player.SetFocus)
        else:
            event.Skip()
            
    def on_wait(self, event):
        self.EndModal(wx.ID_APPLY)
            
    def on_ok(self, event):
        if len(self.players) < 2:
            wx.MessageBox("Oh Anima grande, ci servono almeno due discepoli per far scorrere il sangue!", "Pochi giocatori", wx.OK | wx.ICON_WARNING)
            return
        event.Skip()

class MatchResultDialog(wx.Dialog):
    def __init__(self, parent, match_id, p1, p2, use_defaults=False):
        super().__init__(parent, title="Qual è il verdetto divino?", size=(380, 280))
        self.use_defaults = use_defaults
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        lbl = wx.StaticText(panel, label=f"Partita {match_id}: {p1} contro {p2}\nChi ha trionfato nel tuo nome?")
        vbox.Add(lbl, 0, wx.ALL | wx.EXPAND, 10)
        
        self.rb_result = wx.RadioBox(panel, choices=[p1, p2, "Pareggio"], majorDimension=1, style=wx.RA_SPECIFY_COLS)
        vbox.Add(self.rb_result, 0, wx.ALL | wx.EXPAND, 10)
        
        if not self.use_defaults:
            lbl_pts = wx.StaticText(panel, label="Punti realizzati (o punti per ciascuno in caso di pareggio):")
            vbox.Add(lbl_pts, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
            
            self.txt_pts = wx.TextCtrl(panel, value="0", style=wx.TE_PROCESS_ENTER)
            self.txt_pts.Bind(wx.EVT_TEXT_ENTER, self.on_pts_enter)
            vbox.Add(self.txt_pts, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        else:
            lbl_pts = wx.StaticText(panel, label="I punti verranno assegnati in base alle impostazioni del torneo.")
            vbox.Add(lbl_pts, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
            self.txt_pts = None
            # riduciamo la dimensione della finestra se non serve il campo
            self.SetSize((380, 230))
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, "Suggella il fato!")
        self.btn_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Ripensamento...")
        btn_box.Add(self.btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        
    def on_pts_enter(self, event):
        if self.txt_pts and self.txt_pts.GetValue().strip() != "":
            # Chiamiamo direttamente on_ok per fare la validazione.
            # Se la validazione fallisce, on_ok mostra il messaggio di errore
            # e non chiudiamo il dialogo.
            if self._validate():
                self.EndModal(wx.ID_OK)
        else:
            event.Skip()

    def on_ok(self, event):
        if self._validate():
            event.Skip()
            
    def _validate(self):
        if self.txt_pts:
            val = self.txt_pts.GetValue().strip()
            try:
                float(val)
                return True
            except ValueError:
                wx.MessageBox("Oh creatura imperfetta, i punti devono essere un valore numerico valido!", "Valore Invalido", wx.OK | wx.ICON_WARNING)
                self.txt_pts.SelectAll()
                self.txt_pts.SetFocus()
                return False
        return True
            
    def get_result(self):
        sel = self.rb_result.GetSelection()
        res_str = str(sel + 1)
        if self.txt_pts:
            try:
                pts = float(self.txt_pts.GetValue().strip())
                # Mantieni come intero se non ci sono decimali, altrimenti float
                if pts.is_integer():
                    pts = int(pts)
            except ValueError:
                pts = 0
        else:
            pts = 0 # Non usato
        return res_str, pts

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(parent, title="Le Regole del Sangue", size=(450, 400))
        self.settings = settings
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        lbl_msg = wx.StaticText(panel, label="Mio inflessibile dittatore, decreta come i tuoi sudditi verranno giudicati.")
        vbox.Add(lbl_msg, 0, wx.ALL | wx.EXPAND, 10)
        
        # Criterio Principale
        lbl_main = wx.StaticText(panel, label="Criterio Principale:")
        self.cb_main = wx.Choice(panel, choices=["Vittorie", "Punti Totali"])
        self.cb_main.SetStringSelection(self.settings.main_criterion)
        vbox.Add(lbl_main, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_main, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        # Primo Spareggio
        lbl_tie1 = wx.StaticText(panel, label="Primo Spareggio (Scontri Diretti):")
        self.cb_tie1 = wx.Choice(panel, choices=["Scontro Diretto (Punti)", "Scontro Diretto (Vittorie)"])
        self.cb_tie1.SetStringSelection(self.settings.tiebreaker_1)
        vbox.Add(lbl_tie1, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_tie1, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        # Secondo Spareggio
        lbl_tie2 = wx.StaticText(panel, label="Secondo Spareggio (Totale nel Torneo):")
        self.cb_tie2 = wx.Choice(panel, choices=["Punti Totali", "Vittorie Totali"])
        self.cb_tie2.SetStringSelection(self.settings.tiebreaker_2)
        vbox.Add(lbl_tie2, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_tie2, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        # Divisione Punti
        lbl_split = wx.StaticText(panel, label="In caso di pareggio in partita i punti inseriti verranno:")
        self.cb_split = wx.Choice(panel, choices=["Inserimento Manuale", "Punti Pieni a Entrambi", "Nessun Punto", "Metà ciascuno"])
        self.cb_split.SetStringSelection(self.settings.draw_points_split)
        vbox.Add(lbl_split, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_split, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK, "Che sia Legge!")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Lascia stare")
        btn_box.Add(btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        
    def get_settings(self):
        self.settings.main_criterion = self.cb_main.GetStringSelection()
        self.settings.tiebreaker_1 = self.cb_tie1.GetStringSelection()
        self.settings.tiebreaker_2 = self.cb_tie2.GetStringSelection()
        self.settings.draw_points_split = self.cb_split.GetStringSelection()
        return self.settings

class AddPlayerDialog(wx.Dialog):
    def __init__(self, parent, existing_players):
        super().__init__(parent, title="Nuova Carne da Macello", size=(400, 200))
        self.existing_players = existing_players
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        msg = wx.StaticText(panel, label="Dimmi il nome del nuovo stolto che osa sfidarti:")
        vbox.Add(msg, 0, wx.ALL | wx.EXPAND, 10)
        
        self.txt_player = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.txt_player.Bind(wx.EVT_TEXT_ENTER, self.on_enter)
        vbox.Add(self.txt_player, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, "Aggiungi al Massacro!")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Ripensamento")
        self.btn_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        
        btn_box.Add(self.btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        
    def on_enter(self, event):
        event_ok = wx.CommandEvent(wx.wxEVT_BUTTON, wx.ID_OK)
        self.ProcessEvent(event_ok)
        
    def on_ok(self, event):
        name = self.txt_player.GetValue().strip()
        if len(name) < 3:
            wx.MessageBox("Troppo corto! Almeno 3 caratteri.", "Errore", wx.OK | wx.ICON_WARNING)
            self.txt_player.SelectAll()
            return
        if name in self.existing_players:
            wx.MessageBox("Questo discepolo è già tra noi.", "Errore", wx.OK | wx.ICON_WARNING)
            self.txt_player.SelectAll()
            return
        self.new_name = name
        event.Skip()

class RetirePlayerDialog(wx.Dialog):
    def __init__(self, parent, existing_players):
        super().__init__(parent, title="Sopprimi l'Eretico", size=(400, 200))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        msg = wx.StaticText(panel, label="Chi ha osato fuggire dalla tua ira?")
        vbox.Add(msg, 0, wx.ALL | wx.EXPAND, 10)
        
        self.cb_players = wx.Choice(panel, choices=existing_players)
        if existing_players:
            self.cb_players.SetSelection(0)
        vbox.Add(self.cb_players, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK, "Eliminalo!")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Pietà")
        btn_box.Add(btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        
    def get_selected(self):
        return self.cb_players.GetStringSelection()

class UpdatePlayerDialog(wx.Dialog):
    def __init__(self, parent, player_name, position):
        super().__init__(parent, title="Conferma Aggiornamento", size=(500, 300))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        msg_text = f"Il formidabile {player_name} è già presente negli archivi sacri.\n\nVuoi aggiornare il suo storico e il suo medagliere con il risultato di questo torneo (Posizione {position})?"
        
        # Read-only TextCtrl that is navigable by NVDA
        self.txt_msg = wx.TextCtrl(panel, value=msg_text, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.txt_msg, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_yes = wx.Button(panel, wx.ID_YES, "Sì, Aggiorna!")
        self.btn_no = wx.Button(panel, wx.ID_NO, "No, Salta")
        
        btn_box.Add(self.btn_yes, 0, wx.ALL, 5)
        btn_box.Add(self.btn_no, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        
        self.btn_yes.Bind(wx.EVT_BUTTON, self.on_yes)
        self.btn_no.Bind(wx.EVT_BUTTON, self.on_no)
        
        wx.CallAfter(self.txt_msg.SetFocus)
        
    def on_yes(self, event):
        self.EndModal(wx.ID_YES)
        
    def on_no(self, event):
        self.EndModal(wx.ID_NO)


class PlayerDetailsDialog(wx.Dialog):
    def __init__(self, parent, name, p_data):
        super().__init__(parent, title=f"Dettagli Discepolo: {name}", size=(500, 400))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        m = p_data["medals"]
        num_tornei = len(p_data['history'])
        media = p_data.get('placements_sum', 0) / num_tornei if num_tornei > 0 else 0
        
        lines = []
        lines.append(f"Giocatore: {name}")
        lines.append(f"Medagliere: Oro {m['oro']}, Argento {m['argento']}, Bronzo {m['bronzo']}, Legno {m['legno']}")
        lines.append(f"Media Piazzamenti: {media:.2f} (Tornei giocati: {num_tornei})")
        lines.append("")
        lines.append("Storico Tornei:")
        for h in p_data["history"]:
            lines.append(f"  {h}")
            
        txt_ctrl = wx.TextCtrl(panel, value="\n".join(lines), style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(txt_ctrl, 1, wx.ALL | wx.EXPAND, 10)
        
        btn = wx.Button(panel, wx.ID_OK, "Chiudi")
        vbox.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        
        panel.SetSizer(vbox)
        wx.CallAfter(txt_ctrl.SetFocus)


class ManagePlayersDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Gestione Discepoli", size=(550, 480))
        self.parent = parent
        
        from data import PlayerDB
        self.db = PlayerDB()
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        lbl = wx.StaticText(panel, label="Elenco dei giocatori presenti nel database:")
        vbox.Add(lbl, 0, wx.ALL, 10)
        
        self.list_players = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.update_list()
        vbox.Add(self.list_players, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_details = wx.Button(panel, label="Visualizza Dettagli")
        self.btn_rename = wx.Button(panel, label="Modifica Nome")
        self.btn_delete = wx.Button(panel, label="Elimina Giocatore")
        btn_close = wx.Button(panel, wx.ID_CANCEL, "Chiudi")
        
        self.btn_details.Bind(wx.EVT_BUTTON, self.on_details)
        self.btn_rename.Bind(wx.EVT_BUTTON, self.on_rename)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete)
        
        btn_sizer.Add(self.btn_details, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_rename, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_delete, 0, wx.ALL, 5)
        btn_sizer.Add(btn_close, 0, wx.ALL, 5)
        
        vbox.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        
        wx.CallAfter(self.list_players.SetFocus)
        
    def update_list(self):
        self.list_players.Clear()
        for p in sorted(self.db.players.keys()):
            self.list_players.Append(p)
            
    def on_details(self, event):
        sel = self.list_players.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Seleziona prima un giocatore.", "Attenzione", wx.OK | wx.ICON_WARNING)
            return
        name = self.list_players.GetString(sel)
        dlg = PlayerDetailsDialog(self, name, self.db.players[name])
        dlg.ShowModal()
        dlg.Destroy()
        
    def on_rename(self, event):
        sel = self.list_players.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Seleziona prima un giocatore.", "Attenzione", wx.OK | wx.ICON_WARNING)
            return
        old_name = self.list_players.GetString(sel)
        dlg = wx.TextEntryDialog(self, f"Inserisci il nuovo nome per {old_name}:", "Modifica Nome", old_name)
        if dlg.ShowModal() == wx.ID_OK:
            new_name = dlg.GetValue().strip()
            if not new_name:
                wx.MessageBox("Il nome non può essere vuoto.", "Errore", wx.OK | wx.ICON_ERROR)
                return
            if len(new_name) < 3:
                wx.MessageBox("Nome troppo corto. Servono almeno 3 caratteri.", "Errore", wx.OK | wx.ICON_ERROR)
                return
            if new_name in self.db.players and new_name != old_name:
                wx.MessageBox("Un giocatore con questo nome è già presente nel database.", "Errore", wx.OK | wx.ICON_ERROR)
                return
                
            # Rename key in player database
            data = self.db.players.pop(old_name)
            self.db.players[new_name] = data
            self.db.save()
            
            # Rename in active tournament if present
            main_frame = self.parent
            if hasattr(main_frame, 'tourney') and main_frame.tourney.title:
                tourney_changed = False
                
                # Rename in players
                if old_name in main_frame.tourney.players:
                    stats = main_frame.tourney.players.pop(old_name)
                    main_frame.tourney.players[new_name] = stats
                    tourney_changed = True
                    
                # Rename in played matches
                for m_id, m_data in main_frame.tourney.played_matches.items():
                    if m_data[0] == old_name:
                        m_data[0] = new_name
                        tourney_changed = True
                    if m_data[1] == old_name:
                        m_data[1] = new_name
                        tourney_changed = True
                        
                # Rename in unplayed matches
                for m_id, m_data in main_frame.tourney.unplayed_matches.items():
                    if m_data[0] == old_name:
                        m_data[0] = new_name
                        tourney_changed = True
                    if m_data[1] == old_name:
                        m_data[1] = new_name
                        tourney_changed = True
                        
                # Rename in records_high / records_low
                if main_frame.tourney.records_high[0] == old_name:
                    main_frame.tourney.records_high[0] = new_name
                    tourney_changed = True
                if main_frame.tourney.records_low[0] == old_name:
                    main_frame.tourney.records_low[0] = new_name
                    tourney_changed = True
                    
                if tourney_changed:
                    main_frame.tourney.save()
                    if hasattr(main_frame, 'panel') and main_frame.panel:
                        main_frame.check_state_and_show()
                        
            self.update_list()
            wx.MessageBox(f"Giocatore rinominato in {new_name}.", "Modifica Completata")
        dlg.Destroy()
        
    def on_delete(self, event):
        sel = self.list_players.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Seleziona prima un giocatore.", "Attenzione", wx.OK | wx.ICON_WARNING)
            return
        name = self.list_players.GetString(sel)
        dlg = wx.MessageDialog(self, f"Sei sicuro di voler eliminare definitivamente {name} e tutto il suo storico dal database?\nQuesta azione non può essere annullata.", "Conferma Eliminazione", wx.YES_NO | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_YES:
            self.db.players.pop(name)
            self.db.save()
            self.update_list()
            wx.MessageBox(f"Giocatore {name} rimosso dal database.", "Eliminazione Completata")
        dlg.Destroy()


class HallOfFameDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Classifica Generale (Hall of Fame)", size=(700, 550))
        
        from data import PlayerDB
        self.db = PlayerDB()
        
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        lbl_order = wx.StaticText(panel, label="Ordina per:")
        self.cb_order = wx.Choice(panel, choices=["Nome", "Ori", "Argenti", "Bronzi", "Legni", "Numero Tornei"])
        self.cb_order.SetStringSelection("Ori")
        self.cb_order.Bind(wx.EVT_CHOICE, self.on_update)
        
        lbl_dir = wx.StaticText(panel, label="Direzione:")
        self.cb_dir = wx.Choice(panel, choices=["Discendente (Migliore in cima)", "Ascendente (Peggiore in cima)"])
        self.cb_dir.SetSelection(0)
        self.cb_dir.Bind(wx.EVT_CHOICE, self.on_update)
        
        ctrl_sizer.Add(lbl_order, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_order, 0, wx.ALL, 5)
        ctrl_sizer.Add(lbl_dir, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_dir, 0, wx.ALL, 5)
        
        main_sizer.Add(ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.txt_display = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        font = wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.txt_display.SetFont(font)
        main_sizer.Add(self.txt_display, 1, wx.EXPAND | wx.ALL, 10)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_close = wx.Button(panel, wx.ID_CANCEL, "Chiudi")
        btn_sizer.Add(btn_close, 0, wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        panel.SetSizer(main_sizer)
        self.update_display()
        
        wx.CallAfter(self.txt_display.SetFocus)
        
    def on_update(self, event):
        self.update_display()
        
    def update_display(self):
        order_by = self.cb_order.GetStringSelection()
        reverse = (self.cb_dir.GetSelection() == 0)
        
        flat = []
        for name, p_data in self.db.players.items():
            m = p_data["medals"]
            num_tornei = len(p_data['history'])
            media = p_data.get('placements_sum', 0) / num_tornei if num_tornei > 0 else 0
            
            flat.append({
                'name': name,
                'oro': m['oro'],
                'argento': m['argento'],
                'bronzo': m['bronzo'],
                'legno': m['legno'],
                'tornei': num_tornei,
                'media': media
            })
            
        import functools
        
        def compare_hof(a, b):
            if order_by == "Nome":
                val_a, val_b = a['name'].lower(), b['name'].lower()
            elif order_by == "Ori":
                val_a, val_b = a['oro'], b['oro']
            elif order_by == "Argenti":
                val_a, val_b = a['argento'], b['argento']
            elif order_by == "Bronzi":
                val_a, val_b = a['bronzo'], b['bronzo']
            elif order_by == "Legni":
                val_a, val_b = a['legno'], b['legno']
            elif order_by == "Numero Tornei":
                val_a, val_b = a['tornei'], b['tornei']
            else:
                val_a, val_b = a['oro'], b['oro']
                
            if val_a != val_b:
                return (val_a > val_b) - (val_a < val_b)
                
            # Fallbacks / Tie-breakers
            if order_by != "Ori" and a['oro'] != b['oro']:
                return (a['oro'] > b['oro']) - (a['oro'] < b['oro'])
            if order_by != "Argenti" and a['argento'] != b['argento']:
                return (a['argento'] > b['argento']) - (a['argento'] < b['argento'])
            if order_by != "Bronzi" and a['bronzo'] != b['bronzo']:
                return (a['bronzo'] > b['bronzo']) - (a['bronzo'] < b['bronzo'])
            if order_by != "Legni" and a['legno'] != b['legno']:
                return (a['legno'] > b['legno']) - (a['legno'] < b['legno'])
            if order_by != "Numero Tornei" and a['tornei'] != b['tornei']:
                return (a['tornei'] > b['tornei']) - (a['tornei'] < b['tornei'])
                
            name_cmp = (a['name'] > b['name']) - (a['name'] < b['name'])
            if reverse:
                return -name_cmp
            return name_cmp
            
        flat.sort(key=functools.cmp_to_key(compare_hof), reverse=reverse)
        
        lines = []
        lines.append("CLASSIFICA GENERALE (HALL OF FAME)")
        lines.append("-" * 75)
        lines.append(f"{'Pos':<4} | {'Giocatore':<18} | {'Ori':<4} | {'Arg':<4} | {'Bro':<4} | {'Leg':<4} | {'Tornei':<6} | {'Media Piazz.':<12}")
        lines.append("-" * 75)
        
        for idx, row in enumerate(flat):
            if reverse:
                pos = idx + 1
            else:
                pos = len(flat) - idx
            lines.append(f"{pos:<4} | {row['name']:<18} | {row['oro']:<4} | {row['argento']:<4} | {row['bronzo']:<4} | {row['legno']:<4} | {row['tornei']:<6} | {row['media']:.2f}")
            
        lines.append("-" * 75)
        self.txt_display.SetValue("\n".join(lines))


