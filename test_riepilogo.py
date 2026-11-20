"""Il Riepilogo, dalla 2.18.0: la schermata di Dadillo quando non c'e' niente
da fare, con lo stato del torneo, le cose da fare e le statistiche
dell'archivio (richiesta di Gabriele del 18 novembre 2026).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Le prove sul testo girano dovunque; il pannello vero si apre sul desktop
nascosto di conftest.py, dentro una finestra finta che registra i metodi
chiamati dai pulsanti. L'archivio sta in una cartella di prova.
"""

import datetime
import sys

import pytest

from data import PlayerDB, TournamentData, fields_to_timestamp
from version import VERSION

ADESSO = datetime.datetime(
    2026, 11, 18, 13, 8, tzinfo=datetime.timezone(datetime.timedelta(hours=1))
)
VUOTE = {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0}
PRIMAVERA = "Primavera - martedì 17 marzo 2026 - lunedì 20 aprile 2026"
ESTATE = "Estate - venerdì 1 maggio 2026 - sabato 30 maggio 2026"

finestre_vere = [
    pytest.mark.finestre_vere,
    pytest.mark.skipif(sys.platform != "win32", reason="il desktop nascosto esiste solo in Windows"),
]


def _finestre_vere(funzione):
    for marca in finestre_vere:
        funzione = marca(funzione)
    return funzione


def _archivio(base):
    """Due tornei: Primavera da quattro e Estate da tre, con Anna e Bruno in
    entrambi."""
    db = PlayerDB(base_dir=base)
    storici = {
        "Anna": [f"1° in {PRIMAVERA}", f"2° in {ESTATE}"],
        "Bruno": [f"2° in {PRIMAVERA}", f"1° in {ESTATE}"],
        "Carla": [f"3° in {PRIMAVERA}"],
        "Dario": [f"4° in {PRIMAVERA}"],
        "Elena": [f"3° in {ESTATE}"],
    }
    for nome, storico in storici.items():
        db.players[nome] = {"medals": dict(VUOTE), "history": storico, "placements_sum": 0}
        db.recalculate_player_stats(nome)
    return db


def _torneo(base, stato):
    """Il torneo di prova in uno dei cinque stati del riepilogo."""
    t = TournamentData(base_dir=base)
    if stato == "vuoto":
        return t
    t.title = "Autunno"
    t.start_date = fields_to_timestamp("1/11/2026", "")
    if stato == "preparazione":
        return t
    t.players = {"Anna": [3, 1, 0, 0], "Bruno": [0, 0, 0, 1], "Carla": [0, 0, 0, 0]}
    t.played_matches = {1: ["Anna", "Bruno", "1", 3, 3, 0]}
    if stato == "in_corso":
        t.unplayed_matches = {2: ["Anna", "Carla"], 3: ["Bruno", "Carla"]}
        return t
    t.played_matches[2] = ["Anna", "Carla", "1", 3, 3, 0]
    t.played_matches[3] = ["Bruno", "Carla", "1", 3, 3, 0]
    t.end_date = fields_to_timestamp("15/11/2026", "")
    t.finalized = stato == "finalizzato"
    return t


def test_lo_stato_del_torneo(tmp_path):
    from riepilogo import stato_del_torneo

    base = str(tmp_path)
    for stato in ("vuoto", "preparazione", "in_corso", "concluso", "finalizzato"):
        assert stato_del_torneo(_torneo(base, stato)) == stato


def test_la_data_si_legge_dalla_forma_estesa():
    from riepilogo import data_da_estesa

    assert data_da_estesa("martedì 17 marzo 2026") == datetime.date(2026, 3, 17)
    assert data_da_estesa("Sabato 7 Novembre 2026") == datetime.date(2026, 11, 7)
    assert data_da_estesa("Sconosciuta") is None
    assert data_da_estesa("31 febbraio 2026") is None
    assert data_da_estesa("") is None


def test_un_torneo_di_un_giorno_solo_ha_una_data_sola():
    from riepilogo import _periodo

    assert _periodo("sabato 30 maggio 2026", "sabato 30 maggio 2026") == "giocato sabato 30 maggio 2026"
    assert (
        _periodo("venerdì 1 maggio 2026", "sabato 30 maggio 2026")
        == "da venerdì 1 maggio 2026 a sabato 30 maggio 2026"
    )


def test_il_testo_racconta_l_archivio(tmp_path):
    from riepilogo import testo_riepilogo

    base = str(tmp_path)
    db = _archivio(base)
    righe = testo_riepilogo(db.players, _torneo(base, "vuoto"), ADESSO).split("\n")
    assert righe[0] == f"Dadillo {VERSION}, L'Altare del Sacrificio."
    assert righe[1] == "Mercoledì 18 novembre 2026, ore 13:08."
    assert righe[2] == "L'altare è libero: nessun torneo in corso."
    assert "5 discepoli, 2 tornei e 7 partecipazioni registrate." in righe
    assert (
        "Il più affollato: Primavera con 4 partecipanti; il più intimo: Estate con 3; "
        "in media 3.5 per torneo."
    ) in righe
    assert "Il primo torneo: Primavera, iniziato martedì 17 marzo 2026." in righe
    assert (
        "L'ultimo torneo: Estate, da venerdì 1 maggio 2026 a sabato 30 maggio 2026: "
        "oro a Bruno, argento a Anna, bronzo a Elena."
    ) in righe
    assert "Il torneo più lungo: Primavera, 35 giorni." in righe
    # La vetta per punti: Bruno 56.25 + 100, Anna 100 + 44.4.
    vetta = righe.index("I primi 5 della Hall of Fame, per punti:")
    assert righe[vetta + 1].startswith("1° Bruno: 156.")
    assert righe[vetta + 1].endswith("punti, 1 oro, 1 argento, 2 tornei, media 1.50.")
    assert righe[vetta + 2] == "2° Anna: 144.4 punti, 1 oro, 1 argento, 2 tornei, media 1.50."
    assert righe[vetta + 3] == "3° Carla: 25.0 punti, 1 bronzo, 1 torneo, media 3.00."
    assert righe[vetta + 5] == "5° Dario: 6.2 punti, 1 legno, 1 torneo, media 4.00."
    # Il medagliere: a medaglie pari decidono i punti.
    medagliere = righe.index("I primi 5 del medagliere, ori, poi argenti, bronzi e legni:")
    assert righe[medagliere + 1 : medagliere + 6] == [
        "1. Bruno: 1 oro, 1 argento.",
        "2. Anna: 1 oro, 1 argento.",
        "3. Carla: 1 bronzo.",
        "4. Elena: 1 bronzo.",
        "5. Dario: 1 legno.",
    ]
    curiosita = righe.index("Curiosità:")
    assert righe[curiosita + 1 :] == [
        "Hanno giocato tutti i 2 tornei: Anna e Bruno.",
        "Discepoli con un torneo solo: 3.",
        "Nessuno ha ancora vinto due volte: 2 vincitori diversi in 2 tornei.",
        "La media piazzamenti migliore, con almeno due tornei: Anna e Bruno, 1.50.",
        "Il re del legno: Dario, con 1 quarto posto.",
    ]


def test_il_testo_con_archivi_vuoti(tmp_path):
    from riepilogo import righe_archivio

    assert righe_archivio({}) == [
        "L'archivio dei discepoli:",
        "Ancora nessun discepolo: la Hall of Fame aspetta il primo torneo.",
    ]
    senza_tornei = {"Anna": {"medals": dict(VUOTE), "history": [], "placements_sum": 0}}
    assert righe_archivio(senza_tornei)[1].startswith("1 discepolo e nessun torneo registrato")


def test_le_frasi_e_le_azioni_dei_cinque_stati(tmp_path):
    from riepilogo import AZIONI_COMUNI, righe_stato

    base = str(tmp_path)
    attese = {
        "vuoto": ("L'altare è libero: nessun torneo in corso.", "- Nuovo Torneo, nel menu File o Ctrl+N"),
        "preparazione": ("Il torneo Autunno è in preparazione: mancano i discepoli.", "- Scegli i discepoli"),
        "in_corso": (
            "Torneo in corso: Autunno, 3 discepoli, 1 partita giocata e 2 da giocare, "
            "iniziato domenica 1 novembre 2026.",
            "- Torna alle Partite",
        ),
        "concluso": (
            "Il torneo Autunno è concluso: tutte le 3 partite sono giocate, ma medaglie e "
            "piazzamenti non sono ancora nella Hall of Fame.",
            "- Finalizza il torneo",
        ),
        "finalizzato": (
            "L'ultimo torneo, Autunno, da domenica 1 novembre 2026 a domenica 15 novembre "
            "2026, è concluso e finalizzato: medaglie e piazzamenti sono nella Hall of Fame.",
            "- Classifica finale",
        ),
    }
    for stato, (frase, azione) in attese.items():
        righe = righe_stato(_torneo(base, stato), stato)
        assert righe[0] == frase, stato
        assert righe[1] == "Cosa puoi fare adesso:"
        assert righe[2].startswith(azione), stato
        assert righe[-len(AZIONI_COMUNI) :] == AZIONI_COMUNI


class _FinestraFinta:
    """I metodi della finestra principale che i pulsanti chiamano."""

    def __init__(self):
        self.chiamate = []

    def on_menu_new(self, event=None):
        self.chiamate.append("on_menu_new")

    def resume_setup_players(self):
        self.chiamate.append("resume_setup_players")

    def init_main_ui(self):
        self.chiamate.append("init_main_ui")

    def avvia_finalizzazione(self):
        self.chiamate.append("avvia_finalizzazione")

    def show_standings(self):
        self.chiamate.append("show_standings")


@_finestre_vere
def test_il_pannello_ha_il_testo_e_i_pulsanti_dello_stato(tmp_path):
    import wx

    from riepilogo import PULSANTI, RiepilogoPanel, testo_riepilogo

    class Finestra(wx.Frame, _FinestraFinta):
        def __init__(self):
            wx.Frame.__init__(self, None)
            _FinestraFinta.__init__(self)

    app = wx.App(False)
    base = str(tmp_path)
    db = _archivio(base)
    for stato, pulsanti in PULSANTI.items():
        finestra = Finestra()
        torneo = _torneo(base, stato)
        pannello = RiepilogoPanel(finestra, torneo, db)
        assert pannello.stato == stato
        assert not pannello.txt.IsEditable()
        assert pannello.txt.GetName() == "Riepilogo"
        # Lo stesso testo del generatore, a meno dell'ora.
        testo = pannello.txt.GetValue()
        atteso = testo_riepilogo(db.players, torneo)
        assert testo.split("\n")[2:] == atteso.split("\n")[2:]
        assert [b.GetLabelText() for b in pannello.pulsanti] == [e.replace("&", "") for e, _ in pulsanti]
        for bottone, (_, metodo) in zip(pannello.pulsanti, pulsanti, strict=True):
            bottone.GetEventHandler().ProcessEvent(
                wx.CommandEvent(wx.wxEVT_BUTTON, bottone.GetId())
            )
            assert finestra.chiamate[-1] == metodo
        finestra.Destroy()
    app.Destroy()


def _finestra_principale_nuda(tmp_path):
    """La finestra principale senza il costruttore, che leggerebbe gli
    archivi veri: solo gli attributi che le viste usano."""
    import wx

    from data import SettingsData
    from main_window import MainFrame

    frame = MainFrame.__new__(MainFrame)
    wx.Frame.__init__(frame, None)
    frame.panel = None
    frame.settings = SettingsData(base_dir=str(tmp_path))
    frame.player_db = PlayerDB(base_dir=str(tmp_path))
    return frame


@_finestre_vere
def test_all_avvio_la_vista_segue_lo_stato(tmp_path):
    import wx

    app = wx.App(False)
    base = str(tmp_path)
    frame = _finestra_principale_nuda(tmp_path)
    chiamate = []
    for metodo in ("show_riepilogo", "init_main_ui", "avvia_finalizzazione", "show_standings"):
        setattr(frame, metodo, lambda m=metodo: chiamate.append(m))
    attese = {
        "vuoto": "show_riepilogo",
        "preparazione": "show_riepilogo",
        "in_corso": "init_main_ui",
        "concluso": "avvia_finalizzazione",
        "finalizzato": "show_riepilogo",
    }
    for stato, vista in attese.items():
        frame.tourney = _torneo(base, stato)
        frame.check_state_and_show()
        assert chiamate[-1] == vista, stato
    frame.Destroy()
    app.Destroy()


@_finestre_vere
def test_la_voce_del_menu_visualizza_arriva_al_riepilogo(tmp_path):
    import wx

    app = wx.App(False)
    frame = _finestra_principale_nuda(tmp_path)
    frame.create_menu()
    barra = frame.GetMenuBar()
    visualizza = barra.GetMenu(barra.FindMenu("Visualizza"))
    voci = {voce.GetItemLabelText(): voce.GetId() for voce in visualizza.GetMenuItems()}
    assert list(voci) == ["Classifica", "Riepilogo e statistiche"]
    chiamate = []
    frame.show_riepilogo = lambda: chiamate.append("show_riepilogo")
    frame.ProcessEvent(wx.CommandEvent(wx.wxEVT_MENU, voci["Riepilogo e statistiche"]))
    frame.Destroy()
    app.Destroy()
    assert chiamate == ["show_riepilogo"]


@_finestre_vere
def test_la_finestra_vera_parte_dal_riepilogo(monkeypatch, tmp_path):
    """La finestra principale intera, con gli archivi su una cartella di
    prova: senza torneo mostra il riepilogo, e dopo un Nuovo Torneo
    annullato ci torna."""
    import wx

    import data
    import main_window
    from main_window import MainFrame
    from riepilogo import RiepilogoPanel

    base = str(tmp_path)
    monkeypatch.setattr(data, "APP_DIR", base)
    monkeypatch.setattr(main_window, "DATA_FILE", str(tmp_path / "Dadillo.json"))
    _archivio(base).save()
    app = wx.App(False)
    frame = MainFrame()
    # La vista arriva dalla coda degli eventi, come all'avvio vero.
    app.ProcessPendingEvents()
    wx.Yield()
    assert isinstance(frame.panel, RiepilogoPanel)
    assert frame.panel.stato == "vuoto"
    assert frame.GetTitle().endswith("L'Altare del Sacrificio")
    assert "5 discepoli, 2 tornei e 7 partecipazioni registrate." in frame.panel.txt.GetValue()
    primo = frame.panel

    def annulla():
        for finestra in wx.GetTopLevelWindows():
            if isinstance(finestra, wx.Dialog) and finestra.IsModal():
                finestra.EndModal(wx.ID_CANCEL)

    # Senza torneo Nuovo Torneo non fa domande: apre la creazione, e
    # annullata si torna al riepilogo.
    wx.CallLater(300, annulla)
    frame.on_menu_new()
    assert isinstance(frame.panel, RiepilogoPanel) and frame.panel is not primo
    assert not frame.tourney.title
    frame.Destroy()
    app.Destroy()
