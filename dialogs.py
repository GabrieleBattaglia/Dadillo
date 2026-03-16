import wx

class SetupTournamentDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Nuovo Torneo di Adorazione", size=(450, 350))
        
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
        # Uso TE_MULTILINE ma devo intercettare l'invio se voglio cambiare focus.
        # Oppure uso EVT_KEY_DOWN.
        self.txt_comment = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
        self.txt_comment.Bind(wx.EVT_KEY_DOWN, self.on_comment_key)
        vbox.Add(lbl_comment, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.txt_comment, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, "Sia fatta la tua volontà!")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Pietà, ho cambiato idea!")
        btn_box.Add(self.btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(vbox)
        
    def on_title_enter(self, event):
        self.txt_comment.SetFocus()

    def on_comment_key(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN and not event.ShiftDown():
            # Se premi invio senza shift nel multiline, salta al pulsante OK
            self.btn_ok.SetFocus()
        else:
            event.Skip()

    def get_data(self):
        return self.txt_title.GetValue().strip(), self.txt_comment.GetValue().strip()


class SetupPlayersDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Raduna i Tuoi Discepoli", size=(400, 500))
        
        self.players = []
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        msg = wx.StaticText(panel, label="Mia estremitudine immortale, inserisci i nomi dei tuoi seguaci.")
        vbox.Add(msg, 0, wx.ALL | wx.EXPAND, 10)
        
        self.lbl_player = wx.StaticText(panel, label="Giocatore 1:")
        self.txt_player = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.txt_player.Bind(wx.EVT_TEXT_ENTER, self.on_add_player)
        
        vbox.Add(self.lbl_player, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.txt_player, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        lbl_list = wx.StaticText(panel, label="Lista Discepoli (Premi Canc per sopprimere l'eretico):")
        self.list_players = wx.ListBox(panel, style=wx.LB_SORT | wx.LB_SINGLE)
        self.list_players.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
        vbox.Add(lbl_list, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.list_players, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK, "Tutti pronti al massacro!")
        btn_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Annulla tutto, mio sole!")
        btn_box.Add(btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(vbox)
        
    def on_add_player(self, event):
        name = self.txt_player.GetValue().strip().title()
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
        
        # Ritardo per far aggiornare NVDA senza bloccare la GUI con sleep
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
                # Ritardo anche per la cancellazione
                wx.CallLater(300, self.list_players.SetFocus)
                wx.CallLater(600, self.txt_player.SetFocus)
        else:
            event.Skip()
            
    def on_ok(self, event):
        if len(self.players) < 2:
            wx.MessageBox("Oh Anima grande, ci servono almeno due discepoli per far scorrere il sangue!", "Pochi giocatori", wx.OK | wx.ICON_WARNING)
            return
        event.Skip()

class MatchResultDialog(wx.Dialog):
    def __init__(self, parent, match_id, p1, p2):
        super().__init__(parent, title="Qual è il verdetto divino?", size=(380, 280))
        
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        lbl = wx.StaticText(panel, label=f"Partita {match_id}: {p1} contro {p2}\nChi ha trionfato nel tuo nome?")
        vbox.Add(lbl, 0, wx.ALL | wx.EXPAND, 10)
        
        self.rb_result = wx.RadioBox(panel, choices=[p1, p2, "Pareggio"], majorDimension=1, style=wx.RA_SPECIFY_COLS)
        vbox.Add(self.rb_result, 0, wx.ALL | wx.EXPAND, 10)
        
        lbl_pts = wx.StaticText(panel, label="Punti realizzati (o punti per ciascuno in caso di pareggio):")
        vbox.Add(lbl_pts, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        
        self.txt_pts = wx.TextCtrl(panel, value="0", style=wx.TE_PROCESS_ENTER)
        self.txt_pts.Bind(wx.EVT_TEXT_ENTER, self.on_pts_enter)
        vbox.Add(self.txt_pts, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, "Suggella il fato!")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Ripensamento...")
        btn_box.Add(self.btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)
        
        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        
    def on_pts_enter(self, event):
        if self.txt_pts.GetValue().strip() != "":
            # Simula la pressione del tasto OK per chiudere il dialogo
            event_ok = wx.CommandEvent(wx.wxEVT_BUTTON, wx.ID_OK)
            self.ProcessEvent(event_ok)
        else:
            event.Skip()
        
    def get_result(self):
        sel = self.rb_result.GetSelection()
        res_str = str(sel + 1)
        try:
            pts = int(self.txt_pts.GetValue().strip())
        except ValueError:
            pts = 0
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
        name = self.txt_player.GetValue().strip().title()
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


