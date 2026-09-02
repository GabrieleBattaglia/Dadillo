"""Finestre di dialogo di Dadillo, pensate per la navigazione da tastiera
e per la lettura con screen reader.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import wx

from data import (
    DRAW_SPLITS,
    MAIN_CRITERIA,
    SEARCH_PAIR_MODES,
    TIEBREAKERS_1,
    TIEBREAKERS_2,
    PlayerDB,
    format_date_extended,
    normalize_choice,
    normalize_main_criterion,
    placement_stats,
)
from ui_utils import save_or_warn


class SetupTournamentDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Nuovo Torneo di Adorazione", size=(580, 680))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg = wx.StaticText(
            panel,
            label="Oh mio adorato, supremo Maestro!\nDimmi come vuoi chiamare questo nuovo atto di sottomissione:",
        )
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
        self.cb_type = wx.Choice(
            panel,
            choices=[
                "Girone all'Italiana (Andata e Ritorno)",
                "Girone all'Italiana (Solo Andata)",
            ],
        )
        self.cb_type.SetSelection(0)  # Default: Andata e Ritorno
        vbox.Add(lbl_type, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_type, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # 2. Punteggi Predefiniti
        pts_box = wx.StaticBoxSizer(
            wx.StaticBox(
                panel,
                label="Punteggi Predefiniti (Lascia vuoto per chiedere ogni volta)",
            ),
            wx.HORIZONTAL,
        )

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

        # 3. Criteri di Classifica e Spareggi (v2.6.0)
        rank_box = wx.StaticBoxSizer(
            wx.StaticBox(panel, label="Criteri di Classifica e Spareggi"), wx.VERTICAL
        )

        lbl_main = wx.StaticText(panel, label="Criterio Principale:")
        self.cb_main_criterion = wx.Choice(panel, choices=list(MAIN_CRITERIA))
        self.cb_main_criterion.SetSelection(0)

        lbl_score_dir = wx.StaticText(panel, label="Priorità Punteggio:")
        self.cb_score_direction = wx.Choice(
            panel,
            choices=["Punteggio più alto (Migliore)", "Punteggio più basso (Migliore)"],
        )
        self.cb_score_direction.SetSelection(0)

        lbl_tie1 = wx.StaticText(panel, label="Primo Spareggio (Scontri Diretti):")
        self.cb_tiebreaker_1 = wx.Choice(panel, choices=list(TIEBREAKERS_1))
        self.cb_tiebreaker_1.SetSelection(0)

        lbl_tie2 = wx.StaticText(panel, label="Secondo Spareggio (Totale nel Torneo):")
        self.cb_tiebreaker_2 = wx.Choice(panel, choices=list(TIEBREAKERS_2))
        self.cb_tiebreaker_2.SetSelection(0)

        rank_box.Add(lbl_main, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        rank_box.Add(self.cb_main_criterion, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        rank_box.Add(lbl_score_dir, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        rank_box.Add(self.cb_score_direction, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        rank_box.Add(lbl_tie1, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        rank_box.Add(self.cb_tiebreaker_1, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        rank_box.Add(lbl_tie2, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        rank_box.Add(self.cb_tiebreaker_2, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)

        vbox.Add(rank_box, 0, wx.LEFT | wx.RIGHT | wx.EXPAND | wx.TOP, 10)
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
        for txt, nome in [
            (self.txt_win, "Vittoria"),
            (self.txt_draw, "Pareggio"),
            (self.txt_loss, "Sconfitta"),
        ]:
            val = txt.GetValue().strip()
            if val:
                try:
                    float(val)
                except ValueError:
                    wx.MessageBox(
                        f"Oh fonte di inesauribile calcolo, il punteggio per la {nome} non sembra un numero valido. Puoi perdonare la mia stoltezza e correggerlo?",
                        "Errore di conversione",
                        wx.OK | wx.ICON_ERROR,
                    )
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

        main_criterion = self.cb_main_criterion.GetStringSelection()
        score_dir_idx = self.cb_score_direction.GetSelection()
        score_direction = "Alto" if score_dir_idx == 0 else "Basso"
        tiebreaker_1 = self.cb_tiebreaker_1.GetStringSelection()
        tiebreaker_2 = self.cb_tiebreaker_2.GetStringSelection()

        return (
            title,
            comment,
            tourney_type,
            pts_win,
            pts_draw,
            pts_loss,
            main_criterion,
            score_direction,
            tiebreaker_1,
            tiebreaker_2,
        )


class SetupPlayersDialog(wx.Dialog):
    def __init__(self, parent, existing_players=None, db=None):
        super().__init__(parent, title="Raduna i Tuoi Discepoli", size=(500, 650))

        self.players = existing_players[:] if existing_players else []

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg = wx.StaticText(
            panel,
            label="Mia estremitudine immortale, inserisci i nomi dei tuoi seguaci.",
        )
        vbox.Add(msg, 0, wx.ALL | wx.EXPAND, 10)

        # Listbox per i giocatori del DB
        self.db = db if db is not None else PlayerDB()
        self.all_db_players = sorted(self.db.players.keys())
        db_players = [p for p in self.all_db_players if p not in self.players]

        self.lbl_db = wx.StaticText(panel, label="")
        self.list_db_players = wx.ListBox(
            panel, choices=db_players, style=wx.LB_SINGLE, size=(-1, 120)
        )
        self.update_db_label()
        if db_players:
            self.list_db_players.SetSelection(0)

        self.list_db_players.Bind(wx.EVT_KEY_DOWN, self.on_db_key_down)
        self.list_db_players.Bind(wx.EVT_LISTBOX_DCLICK, self.on_db_dclick)

        vbox.Add(self.lbl_db, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.list_db_players, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        self.lbl_player = wx.StaticText(
            panel, label=f"Giocatore {len(self.players) + 1}:"
        )
        self.txt_player = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.txt_player.Bind(wx.EVT_TEXT_ENTER, self.on_add_player)

        vbox.Add(self.lbl_player, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.txt_player, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        lbl_list = wx.StaticText(
            panel,
            label="Lista Discepoli partecipanti (Premi Canc per sopprimere l'eretico):",
        )
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

    def update_db_label(self):
        count = self.list_db_players.GetCount()
        if count > 0:
            self.lbl_db.SetLabel(
                f"Seleziona dal database ({count} disponibili - Spazio o Doppio Clic per aggiungere):"
            )
        else:
            self.lbl_db.SetLabel("Database locale (0 disponibili):")

    def on_db_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            sel = self.list_db_players.GetSelection()
            if sel != wx.NOT_FOUND:
                self.add_from_db(sel)
        else:
            event.Skip()

    def on_db_dclick(self, event):
        sel = self.list_db_players.GetSelection()
        if sel != wx.NOT_FOUND:
            self.add_from_db(sel)

    def add_from_db(self, sel):
        if sel == wx.NOT_FOUND or sel >= self.list_db_players.GetCount():
            return

        name = self.list_db_players.GetString(sel)
        if name in self.players:
            return

        self.players.append(name)
        self.list_players.Append(name)
        self.lbl_player.SetLabel(f"Giocatore {len(self.players) + 1}:")

        self.list_db_players.Delete(sel)
        self.update_db_label()

        new_count = self.list_db_players.GetCount()
        if new_count > 0:
            new_sel = sel if sel < new_count else new_count - 1
            self.list_db_players.SetSelection(new_sel)
            wx.CallAfter(self.list_db_players.SetFocus)
        else:
            wx.CallAfter(self.txt_player.SetFocus)

    def on_add_player(self, event):
        name = self.txt_player.GetValue().strip()
        if not name:
            return
        if len(name) < 3:
            wx.MessageBox(
                "Oh insondabile pozzo di saggezza,\n"
                "un nome così corto è un insulto\n"
                "alla tua grandezza!\n"
                "Servono almeno 3 caratteri.",
                "Nome troppo corto",
                wx.OK | wx.ICON_WARNING,
            )
            self.txt_player.SelectAll()
            return
        if name in self.players:
            wx.MessageBox(
                f"Mi scudiscio per la vergogna, ma {name} l'abbiamo già convertito al nostro volere.",
                "Nome duplicato",
                wx.OK | wx.ICON_WARNING,
            )
            self.txt_player.SelectAll()
            return

        self.players.append(name)
        self.list_players.Append(name)
        self.txt_player.SetValue("")
        self.lbl_player.SetLabel(f"Giocatore {len(self.players) + 1}:")

        for i in range(self.list_db_players.GetCount()):
            if self.list_db_players.GetString(i) == name:
                self.list_db_players.Delete(i)
                self.update_db_label()
                new_count = self.list_db_players.GetCount()
                if new_count > 0:
                    new_sel = i if i < new_count else new_count - 1
                    self.list_db_players.SetSelection(new_sel)
                break

        # Il focus resta nel campo del nome, pronto per il discepolo successivo.
        # I due spostamenti temporizzati di prima producevano due annunci
        # sovrapposti dello screen reader e potevano rubare i primi caratteri.
        self.txt_player.SetFocus()

    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            sel = self.list_players.GetSelection()
            if sel != wx.NOT_FOUND:
                name = self.list_players.GetString(sel)
                self.players.remove(name)
                self.list_players.Delete(sel)
                self.lbl_player.SetLabel(f"Giocatore {len(self.players) + 1}:")

                if hasattr(self, "all_db_players") and name in self.all_db_players:
                    current_items = [
                        self.list_db_players.GetString(i)
                        for i in range(self.list_db_players.GetCount())
                    ]
                    if name not in current_items:
                        current_items.append(name)
                        current_items.sort()
                        self.list_db_players.Set(current_items)
                        self.update_db_label()
                        try:
                            idx = current_items.index(name)
                            self.list_db_players.SetSelection(idx)
                        except ValueError:
                            pass

                # Il focus resta nell'elenco dei partecipanti, sulla voce che
                # ha preso il posto di quella soppressa, cosi' si puo'
                # continuare a cancellare senza cercare di nuovo la lista.
                rimasti = self.list_players.GetCount()
                if rimasti > 0:
                    self.list_players.SetSelection(min(sel, rimasti - 1))
                self.list_players.SetFocus()
        else:
            event.Skip()

    def on_wait(self, event):
        self.EndModal(wx.ID_APPLY)

    def on_ok(self, event):
        if len(self.players) < 2:
            wx.MessageBox(
                "Oh Anima grande, ci servono almeno due discepoli per far scorrere il sangue!",
                "Pochi giocatori",
                wx.OK | wx.ICON_WARNING,
            )
            return
        event.Skip()


class MatchResultDialog(wx.Dialog):
    def __init__(self, parent, match_id, p1, p2, use_defaults=False):
        super().__init__(parent, title="Qual è il verdetto divino?", size=(380, 280))
        self.use_defaults = use_defaults

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        lbl = wx.StaticText(
            panel,
            label=f"Partita {match_id}: {p1} contro {p2}\nChi ha trionfato nel tuo nome?",
        )
        vbox.Add(lbl, 0, wx.ALL | wx.EXPAND, 10)

        self.rb_result = wx.RadioBox(
            panel,
            choices=[p1, p2, "Pareggio"],
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
        )
        vbox.Add(self.rb_result, 0, wx.ALL | wx.EXPAND, 10)

        if not self.use_defaults:
            lbl_pts = wx.StaticText(
                panel,
                label="Punti realizzati (o punti per ciascuno in caso di pareggio):",
            )
            vbox.Add(lbl_pts, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)

            self.txt_pts = wx.TextCtrl(panel, value="0", style=wx.TE_PROCESS_ENTER)
            self.txt_pts.Bind(wx.EVT_TEXT_ENTER, self.on_pts_enter)
            vbox.Add(self.txt_pts, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        else:
            lbl_pts = wx.StaticText(
                panel,
                label="I punti verranno assegnati in base alle impostazioni del torneo.",
            )
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
                wx.MessageBox(
                    "Oh creatura imperfetta, i punti devono essere un valore numerico valido!",
                    "Valore Invalido",
                    wx.OK | wx.ICON_WARNING,
                )
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
            pts = 0  # Non usato
        return res_str, pts


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super().__init__(parent, title="Le Regole del Sangue", size=(480, 480))
        self.settings = settings

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        lbl_msg = wx.StaticText(
            panel,
            label="Mio inflessibile dittatore, decreta come i tuoi sudditi verranno giudicati.",
        )
        vbox.Add(lbl_msg, 0, wx.ALL | wx.EXPAND, 10)

        # Criterio Principale
        lbl_main = wx.StaticText(panel, label="Criterio Principale:")
        self.cb_main = wx.Choice(panel, choices=list(MAIN_CRITERIA))
        self.cb_main.SetStringSelection(
            normalize_main_criterion(self.settings.main_criterion)
        )
        vbox.Add(lbl_main, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_main, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Priorità Punteggio
        lbl_score_dir = wx.StaticText(panel, label="Priorità Punteggio:")
        self.cb_score_dir = wx.Choice(
            panel,
            choices=["Punteggio più alto (Migliore)", "Punteggio più basso (Migliore)"],
        )
        if getattr(self.settings, "score_direction", "Alto") == "Basso":
            self.cb_score_dir.SetSelection(1)
        else:
            self.cb_score_dir.SetSelection(0)
        vbox.Add(lbl_score_dir, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_score_dir, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Primo Spareggio
        lbl_tie1 = wx.StaticText(panel, label="Primo Spareggio (Scontri Diretti):")
        self.cb_tie1 = wx.Choice(panel, choices=list(TIEBREAKERS_1))
        self.cb_tie1.SetStringSelection(
            normalize_choice(self.settings.tiebreaker_1, TIEBREAKERS_1)
        )
        vbox.Add(lbl_tie1, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_tie1, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Secondo Spareggio
        lbl_tie2 = wx.StaticText(panel, label="Secondo Spareggio (Totale nel Torneo):")
        self.cb_tie2 = wx.Choice(panel, choices=list(TIEBREAKERS_2))
        self.cb_tie2.SetStringSelection(
            normalize_choice(self.settings.tiebreaker_2, TIEBREAKERS_2)
        )
        vbox.Add(lbl_tie2, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_tie2, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Divisione Punti
        lbl_split = wx.StaticText(
            panel, label="In caso di pareggio in partita i punti inseriti verranno:"
        )
        self.cb_split = wx.Choice(panel, choices=list(DRAW_SPLITS))
        self.cb_split.SetStringSelection(
            normalize_choice(self.settings.draw_points_split, DRAW_SPLITS)
        )
        vbox.Add(lbl_split, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_split, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Ricerca con due nomi nelle liste delle partite
        lbl_search = wx.StaticText(
            panel, label="Cercando due nomi nelle liste delle partite:"
        )
        self.cb_search = wx.Choice(panel, choices=list(SEARCH_PAIR_MODES))
        self.cb_search.SetStringSelection(
            normalize_choice(
                getattr(self.settings, "search_pair_mode", None), SEARCH_PAIR_MODES
            )
        )
        vbox.Add(lbl_search, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add(self.cb_search, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK, "Che sia Legge!")
        btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Lascia stare")
        btn_box.Add(btn_ok, 0, wx.ALL, 5)
        btn_box.Add(btn_cancel, 0, wx.ALL, 5)

        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)

    def get_settings(self):
        self.settings.main_criterion = normalize_main_criterion(
            self.cb_main.GetStringSelection()
        )
        self.settings.score_direction = (
            "Alto" if self.cb_score_dir.GetSelection() == 0 else "Basso"
        )
        self.settings.tiebreaker_1 = self.cb_tie1.GetStringSelection()
        self.settings.tiebreaker_2 = self.cb_tie2.GetStringSelection()
        self.settings.draw_points_split = self.cb_split.GetStringSelection()
        self.settings.search_pair_mode = normalize_choice(
            self.cb_search.GetStringSelection(), SEARCH_PAIR_MODES
        )
        return self.settings


class AddPlayerDialog(wx.Dialog):
    def __init__(self, parent, existing_players):
        super().__init__(parent, title="Nuova Carne da Macello", size=(400, 200))
        self.existing_players = existing_players
        self.new_name = ""

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg = wx.StaticText(
            panel, label="Dimmi il nome del nuovo stolto che osa sfidarti:"
        )
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
        # Invio e pulsante devono passare per la stessa validazione: prima
        # l'evento veniva girato al dialogo, che poteva chiudersi saltandola.
        self._conferma()

    def on_ok(self, event):
        self._conferma()

    def _conferma(self):
        """Valida il nome e chiude il dialogo solo se e' accettabile."""
        name = self.txt_player.GetValue().strip()
        if len(name) < 3:
            wx.MessageBox(
                "Nome troppo corto: servono almeno\n3 caratteri.",
                "Errore",
                wx.OK | wx.ICON_WARNING,
            )
            self.txt_player.SelectAll()
            self.txt_player.SetFocus()
            return
        if name in self.existing_players:
            wx.MessageBox(
                "Questo discepolo è già tra noi.", "Errore", wx.OK | wx.ICON_WARNING
            )
            self.txt_player.SelectAll()
            self.txt_player.SetFocus()
            return
        self.new_name = name
        self.EndModal(wx.ID_OK)


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


class TournamentFinalReviewChoiceDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Destino della Hall of Fame", size=(540, 360))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg_text = (
            "Oh mio insigne monarca!\n"
            "L'ultimo dado è stato tratto e tutte\n"
            "le sfide sono concluse. Prima di\n"
            "incidere medaglie e piazzamenti nella\n"
            "Hall of Fame, come devo procedere?\n"
            "Uno per uno: revisiona ogni discepolo\n"
            "e decidi se aggiornarlo o saltarlo.\n"
            "Tutti in massa: immortala subito\n"
            "tutti i partecipanti."
        )

        self.txt_msg = wx.TextCtrl(
            panel, value=msg_text, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH
        )
        vbox.Add(self.txt_msg, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_individual = wx.Button(
            panel, label="Uno per uno (Revisiona discepoli)"
        )
        self.btn_mass = wx.Button(panel, label="Tutti in massa (Aggiorna tutto subito)")
        # Senza un pulsante con identificativo Annulla, wxPython non chiude la
        # finestra con Esc e l'utente resta bloccato: qui c'e' anche la via
        # d'uscita per rinviare la premiazione.
        self.btn_cancel = wx.Button(panel, wx.ID_CANCEL, "Non ora, rimando")

        btn_box.Add(self.btn_individual, 0, wx.ALL, 5)
        btn_box.Add(self.btn_mass, 0, wx.ALL, 5)
        btn_box.Add(self.btn_cancel, 0, wx.ALL, 5)

        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        self.SetEscapeId(wx.ID_CANCEL)

        self.btn_individual.Bind(wx.EVT_BUTTON, self.on_individual)
        self.btn_mass.Bind(wx.EVT_BUTTON, self.on_mass)

        # Nessuna scelta predefinita: chiudere la finestra con Esc deve
        # annullare la premiazione, non farla partire in massa.
        self.choice = None
        wx.CallAfter(self.txt_msg.SetFocus)

    def on_individual(self, event):
        self.choice = "individual"
        self.EndModal(wx.ID_OK)

    def on_mass(self, event):
        self.choice = "mass"
        self.EndModal(wx.ID_OK)


class SinglePlayerReviewDialog(wx.Dialog):
    def __init__(
        self,
        parent,
        player_name,
        position,
        medal_str,
        tourney_title,
        start_date,
        end_date,
        tied_with=None,
    ):
        super().__init__(
            parent, title=f"Aggiornamento Discepolo: {player_name}", size=(500, 320)
        )

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        med_text = f" ({medal_str})" if medal_str else ""
        s_fmt = format_date_extended(start_date)
        e_fmt = format_date_extended(end_date)
        msg_text = (
            f"Discepolo: {player_name}\n"
            f"Posizione ufficiale: {position}° posto{med_text}\n"
            f"Torneo: {tourney_title}\n"
            f"Date: {s_fmt} - {e_fmt}\n"
        )
        if tied_with:
            msg_text += (
                f"Attenzione: a pari merito con\n{', '.join(tied_with)}.\n"
                "La posizione dipende dall'ordine\nalfabetico.\n"
            )
        msg_text += "Confermi questo piazzamento nella\nsacra Hall of Fame?"

        self.txt_msg = wx.TextCtrl(
            panel, value=msg_text, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH
        )
        vbox.Add(self.txt_msg, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, "Sì, Aggiorna Discepolo!")
        self.btn_skip = wx.Button(panel, wx.ID_CANCEL, "Salta Discepolo")

        btn_box.Add(self.btn_ok, 0, wx.ALL, 5)
        btn_box.Add(self.btn_skip, 0, wx.ALL, 5)

        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)

        wx.CallAfter(self.txt_msg.SetFocus)


class MergeSimilarPlayerDialog(wx.Dialog):
    def __init__(self, parent, ext_name, local_name):
        super().__init__(
            parent, title="Risoluzione Similarità Discepoli", size=(560, 380)
        )
        self.ext_name = ext_name
        self.local_name = local_name

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg_text = (
            "Mio onnisciente sovrano!\n"
            "Nel file importato ho scovato il\n"
            f"discepolo {ext_name}, che somiglia\n"
            f"al seguace già registrato {local_name}.\n"
            "Si tratta della stessa persona\n"
            "in carne, ossa e dadi?"
        )

        self.txt_msg = wx.TextCtrl(
            panel, value=msg_text, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH
        )
        vbox.Add(self.txt_msg, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        choices = [
            f"Sì, è la stessa persona! Mantieni nickname locale '{local_name}'",
            f"Sì, è la stessa persona! Usa nickname importato '{ext_name}'",
            "No, sono due eretici distinti! Crea un nuovo discepolo.",
        ]
        self.rb_choices = wx.RadioBox(
            panel,
            label="Come desideri procedere?",
            choices=choices,
            majorDimension=1,
            style=wx.RA_SPECIFY_COLS,
        )
        vbox.Add(self.rb_choices, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_ok = wx.Button(panel, wx.ID_OK, "Conferma Verdetto Divino")
        btn_box.Add(self.btn_ok, 0, wx.ALL, 5)

        vbox.Add(btn_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)

        wx.CallAfter(self.txt_msg.SetFocus)

    def get_result(self):
        sel = self.rb_choices.GetSelection()
        if sel == 0:
            return True, self.local_name
        if sel == 1:
            return True, self.ext_name
        return False, self.ext_name


class UpdatePlayerDialog(wx.Dialog):
    def __init__(self, parent, player_name, position):
        super().__init__(parent, title="Conferma Aggiornamento", size=(500, 300))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg_text = (
            f"Il formidabile {player_name} è già\npresente negli archivi sacri.\n"
            f"Vuoi aggiornare il suo storico e il suo medagliere con il risultato di questo torneo (Posizione {position})?"
        )

        # Read-only TextCtrl that is navigable by NVDA
        self.txt_msg = wx.TextCtrl(
            panel, value=msg_text, style=wx.TE_MULTILINE | wx.TE_READONLY
        )
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
        num_tornei, _, media_testo = placement_stats(p_data)

        lines = []
        lines.append(f"Giocatore: {name}")
        lines.append(f"Medagliere: ori {m['oro']}, argenti {m['argento']},")
        lines.append(f"  bronzi {m['bronzo']}, legni {m['legno']}.")
        lines.append(f"Media piazzamenti {media_testo}, tornei {num_tornei}.")
        lines.append("Storico tornei:")
        for h in p_data["history"]:
            lines.append(f"  {h}")

        txt_ctrl = wx.TextCtrl(
            panel, value="\n".join(lines), style=wx.TE_MULTILINE | wx.TE_READONLY
        )
        vbox.Add(txt_ctrl, 1, wx.ALL | wx.EXPAND, 10)

        btn = wx.Button(panel, wx.ID_OK, "Chiudi")
        vbox.Add(btn, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        panel.SetSizer(vbox)
        wx.CallAfter(txt_ctrl.SetFocus)


class ManagePlayersDialog(wx.Dialog):
    def __init__(self, parent, db=None):
        super().__init__(parent, title="Gestione Discepoli", size=(550, 480))
        self.parent = parent

        # L'archivio arriva dalla finestra principale: una sola copia in memoria,
        # cosi' una rinomina qui si vede subito anche nelle altre finestre.
        self.db = db if db is not None else PlayerDB()

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
            wx.MessageBox(
                "Seleziona prima un giocatore.", "Attenzione", wx.OK | wx.ICON_WARNING
            )
            return
        name = self.list_players.GetString(sel)
        dlg = PlayerDetailsDialog(self, name, self.db.players[name])
        dlg.ShowModal()
        dlg.Destroy()

    def on_rename(self, event):
        sel = self.list_players.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox(
                "Seleziona prima un giocatore.", "Attenzione", wx.OK | wx.ICON_WARNING
            )
            return
        old_name = self.list_players.GetString(sel)
        dlg = wx.TextEntryDialog(
            self, f"Inserisci il nuovo nome per {old_name}:", "Modifica Nome", old_name
        )
        if dlg.ShowModal() == wx.ID_OK:
            new_name = dlg.GetValue().strip()
            if not new_name:
                wx.MessageBox(
                    "Il nome non può essere vuoto.", "Errore", wx.OK | wx.ICON_ERROR
                )
                return
            if len(new_name) < 3:
                wx.MessageBox(
                    "Nome troppo corto. Servono almeno 3 caratteri.",
                    "Errore",
                    wx.OK | wx.ICON_ERROR,
                )
                return
            if new_name in self.db.players and new_name != old_name:
                wx.MessageBox(
                    "Un giocatore con questo nome è già presente nel database.",
                    "Errore",
                    wx.OK | wx.ICON_ERROR,
                )
                return

            # Rename key in player database
            data = self.db.players.pop(old_name)
            self.db.players[new_name] = data

            if not save_or_warn(self.db.save, self):
                # Senza salvataggio l'archivio su disco resta col nome vecchio:
                # annulliamo la rinomina anche in memoria per non lasciare
                # il programma disallineato dai dati salvati.
                self.db.players[old_name] = self.db.players.pop(new_name)
            else:
                # Rename in active tournament if present
                main_frame = self.parent
                if hasattr(main_frame, "tourney") and main_frame.tourney.title:
                    tourney_changed = False

                    # Rename in players
                    if old_name in main_frame.tourney.players:
                        stats = main_frame.tourney.players.pop(old_name)
                        main_frame.tourney.players[new_name] = stats
                        tourney_changed = True

                    # Rename in played matches
                    for m_data in main_frame.tourney.played_matches.values():
                        if m_data[0] == old_name:
                            m_data[0] = new_name
                            tourney_changed = True
                        if m_data[1] == old_name:
                            m_data[1] = new_name
                            tourney_changed = True

                    # Rename in unplayed matches
                    for m_data in main_frame.tourney.unplayed_matches.values():
                        if m_data[0] == old_name:
                            m_data[0] = new_name
                            tourney_changed = True
                        if m_data[1] == old_name:
                            m_data[1] = new_name
                            tourney_changed = True

                    if tourney_changed:
                        save_or_warn(main_frame.tourney.save, self)
                        if hasattr(main_frame, "panel") and main_frame.panel:
                            main_frame.check_state_and_show()

                self.update_list()
                wx.MessageBox(
                    f"Giocatore rinominato in {new_name}.", "Modifica Completata"
                )
        dlg.Destroy()

    def on_delete(self, event):
        sel = self.list_players.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox(
                "Seleziona prima un giocatore.", "Attenzione", wx.OK | wx.ICON_WARNING
            )
            return
        name = self.list_players.GetString(sel)
        dlg = wx.MessageDialog(
            self,
            f"Sei sicuro di voler eliminare {name}\n"
            "e tutto il suo storico dal database?\n"
            "L'azione non può essere annullata.",
            "Conferma Eliminazione",
            wx.YES_NO | wx.ICON_WARNING,
        )
        if dlg.ShowModal() == wx.ID_YES:
            rimosso = self.db.players.pop(name)
            if save_or_warn(self.db.save, self):
                self.update_list()
                wx.MessageBox(
                    f"Giocatore {name} rimosso dal database.", "Eliminazione Completata"
                )
            else:
                # Il salvataggio non e' riuscito: il giocatore torna in archivio
                # perche' su disco non e' mai stato cancellato.
                self.db.players[name] = rimosso
        dlg.Destroy()


class HallOfFameDialog(wx.Dialog):
    def __init__(self, parent, db=None):
        super().__init__(
            parent, title="Classifica Generale (Hall of Fame)", size=(700, 550)
        )

        self.db = db if db is not None else PlayerDB()

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl_order = wx.StaticText(panel, label="Ordina per:")
        self.cb_order = wx.Choice(
            panel,
            choices=["Nome", "Ori", "Argenti", "Bronzi", "Legni", "Numero Tornei"],
        )
        self.cb_order.SetStringSelection("Ori")
        self.cb_order.Bind(wx.EVT_CHOICE, self.on_update)

        lbl_dir = wx.StaticText(panel, label="Direzione:")
        self.cb_dir = wx.Choice(
            panel,
            choices=["Discendente (Migliore in cima)", "Ascendente (Peggiore in cima)"],
        )
        self.cb_dir.SetSelection(0)
        self.cb_dir.Bind(wx.EVT_CHOICE, self.on_update)

        ctrl_sizer.Add(lbl_order, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_order, 0, wx.ALL, 5)
        ctrl_sizer.Add(lbl_dir, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        ctrl_sizer.Add(self.cb_dir, 0, wx.ALL, 5)

        main_sizer.Add(ctrl_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.txt_display = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )
        font = wx.Font(
            11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
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
        reverse = self.cb_dir.GetSelection() == 0

        flat = []
        for name, p_data in self.db.players.items():
            m = p_data["medals"]
            num_tornei, media, media_testo = placement_stats(p_data)

            flat.append(
                {
                    "name": name,
                    "oro": m["oro"],
                    "argento": m["argento"],
                    "bronzo": m["bronzo"],
                    "legno": m["legno"],
                    "tornei": num_tornei,
                    "media": media,
                    "media_testo": media_testo,
                }
            )

        import functools

        def compare_hof(a, b):
            if order_by == "Nome":
                val_a, val_b = a["name"].lower(), b["name"].lower()
            elif order_by == "Ori":
                val_a, val_b = a["oro"], b["oro"]
            elif order_by == "Argenti":
                val_a, val_b = a["argento"], b["argento"]
            elif order_by == "Bronzi":
                val_a, val_b = a["bronzo"], b["bronzo"]
            elif order_by == "Legni":
                val_a, val_b = a["legno"], b["legno"]
            elif order_by == "Numero Tornei":
                val_a, val_b = a["tornei"], b["tornei"]
            else:
                val_a, val_b = a["oro"], b["oro"]

            if val_a != val_b:
                return (val_a > val_b) - (val_a < val_b)

            # Fallbacks / Tie-breakers
            if order_by != "Ori" and a["oro"] != b["oro"]:
                return (a["oro"] > b["oro"]) - (a["oro"] < b["oro"])
            if order_by != "Argenti" and a["argento"] != b["argento"]:
                return (a["argento"] > b["argento"]) - (a["argento"] < b["argento"])
            if order_by != "Bronzi" and a["bronzo"] != b["bronzo"]:
                return (a["bronzo"] > b["bronzo"]) - (a["bronzo"] < b["bronzo"])
            if order_by != "Legni" and a["legno"] != b["legno"]:
                return (a["legno"] > b["legno"]) - (a["legno"] < b["legno"])
            if order_by != "Numero Tornei" and a["tornei"] != b["tornei"]:
                return (a["tornei"] > b["tornei"]) - (a["tornei"] < b["tornei"])

            name_cmp = (a["name"] > b["name"]) - (a["name"] < b["name"])
            if reverse:
                return -name_cmp
            return name_cmp

        flat.sort(key=functools.cmp_to_key(compare_hof), reverse=reverse)

        lines = []
        lines.append("Classifica generale, Hall of Fame")
        lines.append(f"Ordinata per {order_by}, {len(flat)} discepoli")

        # Due righe corte per discepolo, con l'etichetta accanto a ogni numero:
        # la tabella a colonne rendeva il significato dipendente dalla posizione.
        for idx, row in enumerate(flat):
            pos = idx + 1 if reverse else len(flat) - idx
            lines.append(f"{pos}. {row['name']}.")
            lines.append(
                f"  Ori {row['oro']}, argenti {row['argento']}, "
                f"bronzi {row['bronzo']}, legni {row['legno']}."
            )
            lines.append(
                f"  Tornei {row['tornei']}, media piazzamenti {row['media_testo']}."
            )

        self.txt_display.SetValue("\n".join(lines))
