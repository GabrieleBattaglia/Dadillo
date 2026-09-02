"""Finestra principale di Dadillo: menu, elenchi delle partite e comandi.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import itertools
import os

import wx

from data import (
    DATA_FILE,
    SEARCH_PAIR_MODES,
    DataFileError,
    PlayerDB,
    SettingsData,
    TournamentData,
    format_date_extended,
    now_timestamp,
    split_match_points,
)
from dialogs import (
    AddPlayerDialog,
    HallOfFameDialog,
    ManagePlayersDialog,
    MatchResultDialog,
    RetirePlayerDialog,
    SettingsDialog,
    SetupPlayersDialog,
    SetupTournamentDialog,
)
from standings import StandingsPanel
from ui_utils import save_or_warn
from version import VERSION


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(
            None, title=f"Dadillo v{VERSION} - L'Altare del Sacrificio", size=(800, 600)
        )
        self.Maximize(True)
        self.tourney = TournamentData()
        self.settings = SettingsData()
        self.settings.load()

        self.panel = None  # Riferimento al pannello corrente

        # Un solo archivio dei discepoli per tutta l'applicazione: prima ogni
        # finestra ne creava uno suo, rileggendo il file e lavorando su copie
        # che potevano sovrascriversi a vicenda.
        self.player_db = PlayerDB()
        self.check_players_archive()

        try:
            caricato = self.tourney.load()
        except DataFileError as e:
            # Il file del torneo esiste ma non e' leggibile. Una copia e' gia'
            # stata messa da parte: avvisiamo invece di creare un torneo nuovo
            # sopra dati che potrebbero essere ancora recuperabili.
            caricato = False
            wx.MessageBox(
                f"{e}\n"
                "Puoi chiudere ora e tentare il\n"
                "recupero, oppure proseguire e\n"
                "creare un nuovo torneo.",
                "Torneo non leggibile",
                wx.OK | wx.ICON_ERROR,
            )

        if not caricato or not self.tourney.title:
            wx.CallAfter(self.startup_sequence)
        else:
            wx.CallAfter(self.check_state_and_show)

    def check_players_archive(self):
        """Avvisa subito se l'archivio dei discepoli non e' leggibile.
        Finche' resta in questo stato Dadillo rifiuta di salvarlo e di
        esportarlo, per non cancellare la Hall of Fame.
        """
        if self.player_db.load_error:
            wx.MessageBox(
                f"{self.player_db.load_error}\n"
                "Fino al ripristino non registrero'\n"
                "nuove medaglie ne' esportero'\n"
                "il file Giocatori.txt.",
                "Archivio discepoli non leggibile",
                wx.OK | wx.ICON_ERROR,
            )

    def startup_sequence(self):
        dlg1 = SetupTournamentDialog(self)
        if dlg1.ShowModal() == wx.ID_OK:
            (
                title,
                comment,
                t_type,
                p_win,
                p_draw,
                p_loss,
                main_crit,
                score_dir,
                tie1,
                tie2,
            ) = dlg1.get_data()
            if not title:
                title = "Torneo dell'Infinita Clemenza"
            self.tourney.title = title
            self.tourney.comment = comment
            self.tourney.tourney_type = t_type
            self.tourney.pts_win = p_win
            self.tourney.pts_draw = p_draw
            self.tourney.pts_loss = p_loss
            self.tourney.main_criterion = main_crit
            self.tourney.score_direction = score_dir
            self.tourney.tiebreaker_1 = tie1
            self.tourney.tiebreaker_2 = tie2
            dlg1.Destroy()

            wx.CallAfter(self.resume_setup_players)
        else:
            dlg1.Destroy()
            self._show_empty_state()

    def resume_setup_players(self):
        existing_names = list(self.tourney.players.keys())
        dlg2 = SetupPlayersDialog(self, existing_names, db=self.player_db)
        res = dlg2.ShowModal()

        if res == wx.ID_OK:
            self.tourney.players.clear()
            for p in dlg2.players:
                self.tourney.players[p] = [0, 0, 0, 0]  # points, wins, draws, losses

            # Generazione partite
            match_id = 1
            if self.tourney.tourney_type == 1:
                # Solo andata (combinazioni semplici)
                for j in itertools.combinations(self.tourney.players.keys(), 2):
                    self.tourney.unplayed_matches[match_id] = list(j)
                    match_id += 1
            else:
                # Andata e Ritorno (permutazioni)
                for j in itertools.permutations(self.tourney.players.keys(), 2):
                    self.tourney.unplayed_matches[match_id] = list(j)
                    match_id += 1

            self.tourney.start_date = now_timestamp()
            save_or_warn(self.tourney.save, self)
            dlg2.Destroy()
            self.check_state_and_show()

        elif res == wx.ID_APPLY:
            self.tourney.players.clear()
            for p in dlg2.players:
                self.tourney.players[p] = [0, 0, 0, 0]
            save_or_warn(self.tourney.save, self)
            dlg2.Destroy()
            self.Close()

        else:  # CANCEL
            dlg2.Destroy()
            if (
                wx.MessageBox(
                    "Mio insindacabile monarca, annullando ora distruggerai questo torneo in bozza. Sei sicuro?",
                    "Conferma distruzione",
                    wx.YES_NO | wx.ICON_WARNING,
                )
                == wx.YES
            ):
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                self.tourney = TournamentData()
                self._show_empty_state()
            else:
                wx.CallAfter(self.resume_setup_players)

    def _show_empty_state(self):
        if self.panel:
            self.panel.Destroy()
            self.panel = None
        self.panel = wx.Panel(self)
        if not self.GetMenuBar():
            self.create_menu()
        self.SetTitle(f"Dadillo v{VERSION} - L'Altare del Sacrificio")
        msg = wx.StaticText(
            self.panel,
            label="L'Altare è vuoto. Usa il menu File per creare un Nuovo Torneo.",
        )
        font = wx.Font(
            14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD
        )
        msg.SetFont(font)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer()
        sizer.Add(msg, 0, wx.ALIGN_CENTER)
        sizer.AddStretchSpacer()
        self.panel.SetSizer(sizer)
        self.Layout()
        self.Show()

    def check_state_and_show(self):
        if not self.tourney.unplayed_matches and self.tourney.played_matches:
            self.show_standings()
        elif (
            not self.tourney.unplayed_matches
            and not self.tourney.played_matches
            and self.tourney.title
        ):
            self.resume_setup_players()
        else:
            self.init_main_ui()

    def init_main_ui(self):
        self.SetTitle(f"Dadillo v{VERSION} - {self.tourney.title}")
        if self.panel:
            self.panel.Destroy()

        self.panel = wx.Panel(self)
        if not self.GetMenuBar():
            self.create_menu()

        # Ordine di creazione (Z-order) per controllare sia l'ordine di tabulazione
        # sia l'associazione delle etichette (StaticText) per NVDA.
        # NVDA associa il campo al precedente StaticText creato.

        lbl_filter_u = wx.StaticText(
            self.panel, label="Cerca non giocate: <termine> | [<nome1> <nome2>]"
        )
        self.txt_filter_unplayed = wx.TextCtrl(self.panel)

        self.lbl_unplayed = wx.StaticText(self.panel, label="Non giocate...")
        self.list_unplayed = wx.ListBox(self.panel, style=wx.LB_SINGLE)

        self.lbl_played = wx.StaticText(self.panel, label="Giocate...")
        self.list_played = wx.ListBox(self.panel, style=wx.LB_SINGLE)

        lbl_filter_p = wx.StaticText(
            self.panel, label="Cerca giocate: <termine> | [<nome1> <nome2>]"
        )
        self.txt_filter_played = wx.TextCtrl(self.panel)

        self.txt_filter_unplayed.Bind(wx.EVT_TEXT, self.on_filter_change)
        self.txt_filter_played.Bind(wx.EVT_TEXT, self.on_filter_change)
        self.list_unplayed.Bind(wx.EVT_LISTBOX_DCLICK, self.on_match_selected)
        self.list_unplayed.Bind(wx.EVT_CHAR_HOOK, self.on_unplayed_key)
        self.list_played.Bind(wx.EVT_CHAR_HOOK, self.on_played_key)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Pannello Sinistro: Non Giocate
        left_vbox = wx.BoxSizer(wx.VERTICAL)
        left_vbox.Add(self.lbl_unplayed, 0, wx.ALL | wx.EXPAND, 5)

        filter_box_u = wx.BoxSizer(wx.HORIZONTAL)
        filter_box_u.Add(lbl_filter_u, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        filter_box_u.Add(self.txt_filter_unplayed, 1, wx.ALL | wx.EXPAND, 5)
        left_vbox.Add(filter_box_u, 0, wx.EXPAND)

        self.list_unplayed_sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_unplayed_sizer.Add(self.list_unplayed, 1, wx.ALL | wx.EXPAND, 5)

        self.btn_new_tourney = wx.Button(
            self.panel,
            label="Il Torneo è concluso!\nCrea un nuovo evento, oh mio sovrano.",
        )
        self.btn_new_tourney.Bind(wx.EVT_BUTTON, self.on_menu_new)
        self.btn_new_tourney.Hide()  # Nascosto di default

        # Aggiungiamo sia la lista che il pulsante, li gestiremo dinamicamente in update_lists
        left_vbox.Add(self.list_unplayed_sizer, 1, wx.EXPAND)
        left_vbox.Add(self.btn_new_tourney, 1, wx.EXPAND | wx.ALL, 20)

        main_sizer.Add(left_vbox, 1, wx.EXPAND | wx.ALL, 10)
        # Pannello Destro: Giocate
        right_vbox = wx.BoxSizer(wx.VERTICAL)
        right_vbox.Add(self.lbl_played, 0, wx.ALL | wx.EXPAND, 5)

        filter_box_p = wx.BoxSizer(wx.HORIZONTAL)
        filter_box_p.Add(lbl_filter_p, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        filter_box_p.Add(self.txt_filter_played, 1, wx.ALL | wx.EXPAND, 5)

        right_vbox.Add(filter_box_p, 0, wx.EXPAND)

        right_vbox.Add(self.list_played, 1, wx.ALL | wx.EXPAND, 5)

        main_sizer.Add(right_vbox, 1, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(main_sizer)
        self.update_lists()
        self.Layout()
        self.Show()

        # Forza il focus per lo screen reader dopo aver costruito l'interfaccia
        wx.CallAfter(self.list_unplayed.SetFocus)

    def create_menu(self):
        menubar = wx.MenuBar()

        menu_file = wx.Menu()
        item_new = menu_file.Append(wx.ID_ANY, "Nuovo Torneo\tCtrl+N")
        item_save = menu_file.Append(wx.ID_ANY, "Salva\tCtrl+S")
        menu_file.AppendSeparator()
        item_save_unplayed = menu_file.Append(wx.ID_ANY, "Salva lista non giocate")
        item_save_played = menu_file.Append(wx.ID_ANY, "Salva lista giocate")
        menu_file.AppendSeparator()
        item_exit = menu_file.Append(wx.ID_ANY, "Esci\tCtrl+Q")

        menu_view = wx.Menu()
        item_standings = menu_view.Append(wx.ID_ANY, "Classifica Parziale\tCtrl+L")

        menu_players = wx.Menu()
        item_add = menu_players.Append(wx.ID_ANY, "Aggiungi Giocatore al Torneo")
        item_retire = menu_players.Append(wx.ID_ANY, "Ritira Giocatore dal Torneo")
        menu_players.AppendSeparator()
        item_manage_db = menu_players.Append(wx.ID_ANY, "Gestione Giocatori DB")
        item_hof = menu_players.Append(wx.ID_ANY, "Classifica Generale (Hall of Fame)")
        item_export_hof = menu_players.Append(
            wx.ID_ANY, "Esporta Hall of Fame (Giocatori.txt)"
        )

        menu_options = wx.Menu()
        item_rules = menu_options.Append(wx.ID_ANY, "Regole Torneo")
        item_merge = menu_options.Append(wx.ID_ANY, "Unisci Database Giocatori")

        menubar.Append(menu_file, "File")
        menubar.Append(menu_view, "Visualizza")
        menubar.Append(menu_players, "Giocatori")
        menubar.Append(menu_options, "Opzioni")

        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.on_menu_new, item_new)
        self.Bind(wx.EVT_MENU, self.on_menu_save, item_save)
        self.Bind(wx.EVT_MENU, self.on_menu_save_unplayed, item_save_unplayed)
        self.Bind(wx.EVT_MENU, self.on_menu_save_played, item_save_played)
        self.Bind(wx.EVT_MENU, self.on_menu_exit, item_exit)
        self.Bind(wx.EVT_MENU, self.on_menu_standings, item_standings)
        self.Bind(wx.EVT_MENU, self.on_menu_add_player, item_add)
        self.Bind(wx.EVT_MENU, self.on_menu_retire_player, item_retire)
        self.Bind(wx.EVT_MENU, self.on_menu_manage_db, item_manage_db)
        self.Bind(wx.EVT_MENU, self.on_menu_hof, item_hof)
        self.Bind(wx.EVT_MENU, self.on_menu_export_hof, item_export_hof)
        self.Bind(wx.EVT_MENU, self.on_menu_merge_db, item_merge)
        self.Bind(wx.EVT_MENU, self.on_menu_rules, item_rules)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        if not save_or_warn(self.tourney.save, self) and event.CanVeto():
            risposta = wx.MessageBox(
                "Il torneo non e' stato salvato.\n"
                "Vuoi uscire lo stesso e perdere\n"
                "le ultime modifiche?",
                "Uscita senza salvataggio",
                wx.YES_NO | wx.ICON_WARNING,
            )
            if risposta != wx.YES:
                event.Veto()
                return
        event.Skip()

    def on_menu_standings(self, event):
        if not self.tourney.played_matches:
            wx.MessageBox(
                "Nessuna partita è stata ancora giocata. L'Altare attende il primo sacrificio!",
                "Attesa",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        self.show_standings(is_final=False)

    def on_filter_change(self, event):
        # Si ricostruisce solo la lista del campo che e' stato modificato,
        # non entrambe a ogni carattere digitato.
        if event.GetEventObject() is self.txt_filter_played:
            self.fill_played_list()
        else:
            self.fill_unplayed_list()

    def update_lists(self):
        tot_unplayed = len(self.tourney.unplayed_matches)
        tot_played = len(self.tourney.played_matches)
        tot_matches = tot_unplayed + tot_played

        if tot_matches > 0:
            perc_unplayed = (tot_unplayed / tot_matches) * 100
            perc_played = (tot_played / tot_matches) * 100
        else:
            perc_unplayed = perc_played = 0.0

        self.lbl_unplayed.SetLabel(
            f"Non giocate {tot_unplayed} su {tot_matches}: {perc_unplayed:.1f}%"
        )
        self.lbl_played.SetLabel(
            f"Giocate {tot_played} su {tot_matches}: {perc_played:.1f}%"
        )

        if tot_unplayed == 0:
            if hasattr(self, "list_unplayed_sizer"):
                self.list_unplayed_sizer.ShowItems(False)
            if hasattr(self, "btn_new_tourney"):
                self.btn_new_tourney.Show()
        else:
            if hasattr(self, "list_unplayed_sizer"):
                self.list_unplayed_sizer.ShowItems(True)
            if hasattr(self, "btn_new_tourney"):
                self.btn_new_tourney.Hide()

        # Forza un ricalcolo del layout
        if self.panel:
            self.panel.Layout()

        self.fill_unplayed_list()
        self.fill_played_list()

    @staticmethod
    def match_filter(text, p1, p2, filt_str, coppia_in_qualsiasi_ordine=True):
        """Vero se la partita passa il filtro di ricerca.
        Con un solo termine cerca ovunque nella riga. Con due nomi cerca la
        coppia in entrambi gli ordini, quindi trova anche la partita di ritorno,
        oppure rispetta l'ordine scritto, secondo l'impostazione scelta.
        """
        if not filt_str:
            return True
        parts = filt_str.split()
        if len(parts) == 1:
            return parts[0] in text.lower()
        s1, s2 = parts[0], parts[1]
        p1_low = p1.lower()
        p2_low = p2.lower()
        diretto = s1 in p1_low and s2 in p2_low
        if not coppia_in_qualsiasi_ordine:
            return diretto
        return diretto or (s1 in p2_low and s2 in p1_low)

    def coppia_in_qualsiasi_ordine(self):
        """Vero se la ricerca per due nomi ignora l'ordine in cui sono scritti."""
        return (
            getattr(self.settings, "search_pair_mode", SEARCH_PAIR_MODES[0])
            == SEARCH_PAIR_MODES[0]
        )

    def fill_unplayed_list(self):
        """Ricostruisce la sola lista delle partite da giocare."""
        self.list_unplayed.Clear()
        filt_u = self.txt_filter_unplayed.GetValue().strip().lower()
        in_qualsiasi_ordine = self.coppia_in_qualsiasi_ordine()
        for m_id, (p1, p2) in sorted(self.tourney.unplayed_matches.items()):
            text = f"({m_id}) {p1} vs {p2}"
            if self.match_filter(text, p1, p2, filt_u, in_qualsiasi_ordine):
                self.list_unplayed.Append(text, m_id)

    def fill_played_list(self):
        """Ricostruisce la sola lista delle partite giocate."""
        self.list_played.Clear()
        filt_p = self.txt_filter_played.GetValue().strip().lower()
        in_qualsiasi_ordine = self.coppia_in_qualsiasi_ordine()
        # Mostriamo le partite giocate in ordine inverso (l'ultima giocata in cima)
        # In Python 3.7+ i dizionari preservano l'ordine di inserimento.
        for m_id, data in reversed(list(self.tourney.played_matches.items())):
            p1, p2, res, pts = data[:4]
            if res == "1":
                winner = f"Vince {p1}"
            elif res == "2":
                winner = f"Vince {p2}"
            else:
                winner = "Pareggio"
            text = f"({m_id}) {p1} vs {p2} - {winner} (Punti base: {pts})"
            if self.match_filter(text, p1, p2, filt_p, in_qualsiasi_ordine):
                self.list_played.Append(text, m_id)

    def on_unplayed_key(self, event):
        if event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.process_selected_unplayed()
        else:
            event.Skip()

    def on_match_selected(self, event):
        self.process_selected_unplayed()

    def draw_split(self):
        """Regola di ripartizione dei punti in caso di pareggio.
        Conta quella del torneo in corso, che ogni torneo salva nel proprio
        file; le impostazioni generali valgono solo per i tornei che non la
        hanno registrata.
        """
        return getattr(self.tourney, "draw_points_split", None) or getattr(
            self.settings, "draw_points_split", "Inserimento Manuale"
        )

    def _get_draw_points(self, pts):
        # Regola unica, condivisa con la classifica: vedi split_match_points.
        return split_match_points("3", pts, self.draw_split())

    def process_selected_unplayed(self):
        sel = self.list_unplayed.GetSelection()
        if sel == wx.NOT_FOUND:
            return

        m_id = self.list_unplayed.GetClientData(sel)
        p1, p2 = self.tourney.unplayed_matches[m_id]

        use_def = (
            self.tourney.pts_win is not None
            or self.tourney.pts_draw is not None
            or self.tourney.pts_loss is not None
        )

        dlg = MatchResultDialog(self, m_id, p1, p2, use_defaults=use_def)
        if dlg.ShowModal() == wx.ID_OK:
            res, pts = dlg.get_result()

            # Calcolo dei punti effettivi
            pt1 = 0
            pt2 = 0

            if res == "1":
                pt1 = self.tourney.pts_win if self.tourney.pts_win is not None else pts
                pt2 = self.tourney.pts_loss if self.tourney.pts_loss is not None else 0
                self.tourney.players[p1][1] += 1
                self.tourney.players[p2][3] += 1
            elif res == "2":
                pt2 = self.tourney.pts_win if self.tourney.pts_win is not None else pts
                pt1 = self.tourney.pts_loss if self.tourney.pts_loss is not None else 0
                self.tourney.players[p2][1] += 1
                self.tourney.players[p1][3] += 1
            elif res == "3":
                if self.tourney.pts_draw is not None:
                    pt1 = pt2 = self.tourney.pts_draw
                else:
                    pt1, pt2 = self._get_draw_points(pts)

                self.tourney.players[p1][2] += 1
                self.tourney.players[p2][2] += 1

            self.tourney.players[p1][0] += pt1
            self.tourney.players[p2][0] += pt2

            # Salviamo nel DB il pts originale se c'era, oppure il max tra pt1 e pt2 come riferimento per i record
            save_pts = pts if not use_def else max(pt1, pt2)
            # Dalla 2.1.0 possiamo estendere il formato dei dati giocati aggiungendo pt1 e pt2 per non ricalcolarli,
            # ma lo appendiamo alla fine per retrocompatibilità.
            self.tourney.played_matches[m_id] = [p1, p2, res, save_pts, pt1, pt2]
            del self.tourney.unplayed_matches[m_id]

            save_or_warn(self.tourney.save, self)

            self.update_lists()
            self.list_unplayed.SetFocus()

            if len(self.tourney.unplayed_matches) == 0:
                self.tourney.end_date = now_timestamp()
                save_or_warn(self.tourney.save, self)
                wx.MessageBox(
                    "Oh insuperabile divinità, tutte le battaglie sono concluse! Ti accompagno alla sala delle classifiche.",
                    "Torneo Concluso",
                )
                self.show_standings()

        dlg.Destroy()

    def on_played_key(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            sel = self.list_played.GetSelection()
            if sel == wx.NOT_FOUND:
                return

            m_id = self.list_played.GetClientData(sel)
            data = self.tourney.played_matches.get(m_id)
            if not data:
                return

            # Un giocatore ritirato resta nelle partite gia' giocate ma non e'
            # piu' fra i partecipanti: senza questo controllo il ripristino dei
            # punteggi si interrompeva a meta', lasciando i dati incoerenti.
            mancanti = [n for n in (data[0], data[1]) if n not in self.tourney.players]
            if mancanti:
                wx.MessageBox(
                    "Non posso annullare questa partita.\n"
                    f"{', '.join(mancanti)} non fa piu'\n"
                    "parte del torneo, quindi i punteggi\n"
                    "non tornerebbero al loro posto.",
                    "Annullamento impossibile",
                    wx.OK | wx.ICON_WARNING,
                )
                return

            if (
                wx.MessageBox(
                    "Mio padrone, sei sicuro di voler annullare questo risultato e riportare la partita tra le non giocate?",
                    "Conferma annullamento",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                == wx.YES
            ):
                # Retrocompatibilità: se la lista ha 4 elementi (vecchi tornei)
                if len(data) == 4:
                    p1, p2, res, pts = data
                    if res == "1":
                        pt1, pt2 = pts, 0
                    elif res == "2":
                        pt1, pt2 = 0, pts
                    else:
                        pt1, pt2 = self._get_draw_points(pts)
                else:
                    # Nuovi tornei (v2.1.0+): [p1, p2, res, save_pts, pt1, pt2]
                    p1, p2, res, pts, pt1, pt2 = data

                if res == "1":
                    self.tourney.players[p1][1] -= 1
                    self.tourney.players[p2][3] -= 1
                elif res == "2":
                    self.tourney.players[p2][1] -= 1
                    self.tourney.players[p1][3] -= 1
                elif res == "3":
                    self.tourney.players[p1][2] -= 1
                    self.tourney.players[p2][2] -= 1

                self.tourney.players[p1][0] -= pt1
                self.tourney.players[p2][0] -= pt2

                self.tourney.unplayed_matches[m_id] = [p1, p2]
                del self.tourney.played_matches[m_id]
                save_or_warn(self.tourney.save, self)
                self.update_lists()
                self.list_played.SetFocus()
        else:
            event.Skip()

    def show_standings(self, is_final=True):
        if self.panel:
            self.panel.Destroy()
        self.panel = StandingsPanel(
            self, self.tourney, self.settings, is_final=is_final
        )
        if not self.GetMenuBar():
            self.create_menu()
        self.Layout()
        self.Show()
        # Forza il focus per lo screen reader dopo aver costruito l'interfaccia
        wx.CallAfter(self.panel.txt_display.SetFocus)

    def on_menu_new(self, event):
        if (
            wx.MessageBox(
                "Mio incommensurabile sovrano, azzerare tutto e iniziare un nuovo torneo?",
                "Nuovo Torneo",
                wx.YES_NO | wx.ICON_WARNING,
            )
            == wx.YES
        ):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            self.tourney = TournamentData()
            self.panel.Destroy()
            self.startup_sequence()

    def on_menu_save(self, event):
        if save_or_warn(self.tourney.save, self):
            wx.MessageBox(
                "La tua volontà è stata incisa nella pietra digitale.", "Salvato"
            )

    def on_menu_save_unplayed(self, event):
        tot_unplayed = len(self.tourney.unplayed_matches)
        tot_played = len(self.tourney.played_matches)
        tot_matches = tot_unplayed + tot_played

        safe_title = "".join(
            [c for c in self.tourney.title if c.isalpha() or c.isdigit() or c == " "]
        ).rstrip()
        filename = f"{safe_title}_non_giocate_{tot_unplayed}su{tot_matches}.txt"

        # Salviamo nella stessa cartella del programma
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Torneo: {self.tourney.title}\n")
                f.write(
                    f"Data inizio: {format_date_extended(self.tourney.start_date)}\n"
                )
                if self.tourney.comment:
                    f.write(f"Note: {self.tourney.comment}\n")
                f.write(f"Partite non giocate: {tot_unplayed} su {tot_matches}.\n")

                f.writelines(
                    f"({m_id}) {p1} vs {p2}\n"
                    for m_id, (p1, p2) in sorted(self.tourney.unplayed_matches.items())
                )

            wx.MessageBox(
                f"Lista partite non giocate salvata con successo in:\n{filepath}",
                "Salvataggio completato",
                wx.OK | wx.ICON_INFORMATION,
            )
        except (OSError, UnicodeError) as e:
            wx.MessageBox(
                f"Errore durante il salvataggio:\n{e!s}",
                "Errore",
                wx.OK | wx.ICON_ERROR,
            )

    def on_menu_save_played(self, event):
        tot_unplayed = len(self.tourney.unplayed_matches)
        tot_played = len(self.tourney.played_matches)
        tot_matches = tot_unplayed + tot_played

        safe_title = "".join(
            [c for c in self.tourney.title if c.isalpha() or c.isdigit() or c == " "]
        ).rstrip()
        filename = f"{safe_title}_giocate_{tot_played}su{tot_matches}.txt"

        # Salviamo nella stessa cartella del programma
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Torneo: {self.tourney.title}\n")
                f.write(
                    f"Data inizio: {format_date_extended(self.tourney.start_date)}\n"
                )
                if self.tourney.comment:
                    f.write(f"Note: {self.tourney.comment}\n")
                f.write(f"Partite giocate: {tot_played} su {tot_matches}.\n")

                for m_id, data in reversed(list(self.tourney.played_matches.items())):
                    p1, p2, res, pts = data[:4]
                    if res == "1":
                        winner = f"Vince {p1}"
                    elif res == "2":
                        winner = f"Vince {p2}"
                    else:
                        winner = "Pareggio"
                    f.write(f"({m_id}) {p1} vs {p2} - {winner} (Punti base: {pts})\n")

            wx.MessageBox(
                f"Lista partite giocate salvata con successo in:\n{filepath}",
                "Salvataggio completato",
                wx.OK | wx.ICON_INFORMATION,
            )
        except (OSError, UnicodeError) as e:
            wx.MessageBox(
                f"Errore durante il salvataggio:\n{e!s}",
                "Errore",
                wx.OK | wx.ICON_ERROR,
            )

    def on_menu_exit(self, event):
        save_or_warn(self.tourney.save, self)
        save_or_warn(self.player_db.export_to_txt, self)
        self.Close()

    def on_menu_merge_db(self, event):
        with wx.FileDialog(
            self,
            "Seleziona il file Dadillo_players.json da fondere",
            wildcard="File JSON (*.json)|*.json",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()

            from dialogs import MergeSimilarPlayerDialog

            def interactive_resolver(ext_name, candidate_name):
                dlg = MergeSimilarPlayerDialog(self, ext_name, candidate_name)
                dlg.ShowModal()
                is_same, chosen = dlg.get_result()
                dlg.Destroy()
                return is_same, chosen

            _success, log = self.player_db.merge_db(
                pathname, interactive_resolver=interactive_resolver
            )

            self.show_merge_summary("\n".join(log))

    def show_merge_summary(self, log_text):
        dlg = wx.Dialog(
            self,
            title="Resoconto Fusione Database",
            size=(600, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        vbox = wx.BoxSizer(wx.VERTICAL)

        lbl = wx.StaticText(dlg, label="Ecco il riepilogo delle operazioni eseguite:")
        vbox.Add(lbl, 0, wx.ALL, 10)

        txt = wx.TextCtrl(dlg, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH)
        txt.SetValue(log_text)
        vbox.Add(txt, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_ok = wx.Button(dlg, wx.ID_OK, label="Chiudi")
        vbox.Add(btn_ok, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        dlg.SetSizer(vbox)
        dlg.Layout()

        # Forza focus sul text ctrl per accessibilità
        wx.CallAfter(txt.SetFocus)

        dlg.ShowModal()
        dlg.Destroy()

    def on_menu_add_player(self, event):
        if not self.tourney.unplayed_matches and self.tourney.played_matches:
            wx.MessageBox(
                "Oh possente, il torneo è già concluso. Inizia un nuovo torneo per aggiungere vittime.",
                "Troppo tardi",
                wx.OK | wx.ICON_INFORMATION,
            )
            return

        dlg = AddPlayerDialog(self, list(self.tourney.players.keys()))
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.new_name
            self.tourney.players[name] = [0, 0, 0, 0]

            existing_players = [p for p in self.tourney.players if p != name]

            # Trova l'id massimo attuale
            all_ids = list(self.tourney.unplayed_matches) + list(
                self.tourney.played_matches
            )
            max_id = max(all_ids) if all_ids else 0

            for p in existing_players:
                if self.tourney.tourney_type == 1:
                    # Solo andata
                    max_id += 1
                    self.tourney.unplayed_matches[max_id] = [name, p]
                else:
                    # Andata e ritorno
                    max_id += 1
                    self.tourney.unplayed_matches[max_id] = [name, p]
                    max_id += 1
                    self.tourney.unplayed_matches[max_id] = [p, name]

            save_or_warn(self.tourney.save, self)
            self.update_lists()

            num_matches = (
                len(existing_players)
                if self.tourney.tourney_type == 1
                else len(existing_players) * 2
            )
            wx.MessageBox(
                f"Il nuovo stolto {name} è stato gettato nell'arena. Sono state generate {num_matches} nuove sfide.",
                "Vittima Aggiunta",
            )
        dlg.Destroy()

    def on_menu_retire_player(self, event):
        if not self.tourney.unplayed_matches and self.tourney.played_matches:
            wx.MessageBox(
                "Nessuno può più fuggire, il torneo è terminato.",
                "Troppo tardi",
                wx.OK | wx.ICON_INFORMATION,
            )
            return

        dlg = RetirePlayerDialog(self, list(self.tourney.players.keys()))
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.get_selected()
            if not name:
                dlg.Destroy()
                return

            if (
                wx.MessageBox(
                    f"Sei certo di voler sopprimere {name}? Perderà a tavolino tutte le partite rimanenti e verrà cancellato dalla classifica.",
                    "Conferma Soppressione",
                    wx.YES_NO | wx.ICON_WARNING,
                )
                == wx.YES
            ):
                to_delete = []
                # Trova tutte le sue partite non giocate e assegna vittoria a tavolino all'avversario
                for m_id, (p1, p2) in self.tourney.unplayed_matches.items():
                    if p1 == name:
                        to_delete.append((m_id, p2, "2"))
                    elif p2 == name:
                        to_delete.append((m_id, p1, "1"))

                for m_id, opp, res in to_delete:
                    # L'avversario prende la vittoria ma nessun punto (per evitare di falsare le statistiche punti totali)
                    self.tourney.players[opp][1] += 1

                    p1, p2 = self.tourney.unplayed_matches[m_id]
                    # Record completo fin da subito: 0 punti a tavolino
                    self.tourney.played_matches[m_id] = [p1, p2, res, 0, 0, 0]
                    del self.tourney.unplayed_matches[m_id]

                # Rimuovi il giocatore dalle statistiche (non apparirà più in classifica)
                del self.tourney.players[name]

                save_or_warn(self.tourney.save, self)
                self.update_lists()
                wx.MessageBox(
                    f"{name} è stato soppresso. Sono state assegnate a tavolino {len(to_delete)} vittorie ai suoi avversari.",
                    "Esecuzione Completata",
                )

                if len(self.tourney.unplayed_matches) == 0:
                    self.tourney.end_date = now_timestamp()
                    save_or_warn(self.tourney.save, self)
                    wx.MessageBox(
                        "Questa esecuzione ha concluso le battaglie! Ti accompagno alla sala delle classifiche.",
                        "Torneo Concluso",
                    )
                    self.show_standings()

        dlg.Destroy()

    def on_menu_rules(self, event):
        dlg = SettingsDialog(self, self.settings)
        if dlg.ShowModal() == wx.ID_OK:
            self.settings = dlg.get_settings()
            save_or_warn(self.settings.save, self)
            # Le nuove regole valgono di sicuro per i tornei futuri. Applicarle
            # al torneo in corso cambia la classifica gia' consultata, quindi
            # va chiesto invece di farlo in silenzio.
            if self.tourney and self.tourney.title:
                risposta = wx.MessageBox(
                    "Le nuove regole valgono per i\n"
                    "prossimi tornei. Vuoi applicarle\n"
                    f"anche al torneo in corso,\n{self.tourney.title}?\n"
                    "La classifica potrebbe cambiare.",
                    "Regole del torneo in corso",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                if risposta == wx.YES:
                    self.tourney.main_criterion = self.settings.main_criterion
                    self.tourney.score_direction = getattr(
                        self.settings, "score_direction", "Alto"
                    )
                    self.tourney.tiebreaker_1 = self.settings.tiebreaker_1
                    self.tourney.tiebreaker_2 = self.settings.tiebreaker_2
                    self.tourney.draw_points_split = self.settings.draw_points_split
                    save_or_warn(self.tourney.save, self)
        dlg.Destroy()

    def on_menu_manage_db(self, event):
        dlg = ManagePlayersDialog(self, db=self.player_db)
        dlg.ShowModal()
        dlg.Destroy()

    def on_menu_hof(self, event):
        dlg = HallOfFameDialog(self, db=self.player_db)
        dlg.ShowModal()
        dlg.Destroy()

    def on_menu_export_hof(self, event):
        if save_or_warn(self.player_db.export_to_txt, self):
            wx.MessageBox(
                "File Giocatori.txt esportato con successo!",
                "Esportazione Completata",
                wx.OK | wx.ICON_INFORMATION,
            )
