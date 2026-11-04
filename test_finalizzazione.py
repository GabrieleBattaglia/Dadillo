"""La finalizzazione prima della classifica finale, dalla 2.16.0 (issue 16).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Le finestre vere si aprono sul desktop nascosto di conftest.py. Dove serve
una risposta, la finestra di finalizzazione e quella della revisione sono
sostituite da copie finte che rispondono da sole, e i messaggi di wx si
raccolgono invece di aprirsi. Torneo e archivio stanno in una cartella di
prova: niente di vero si legge o si scrive accanto al programma.
"""

import json
import sys

import pytest

from data import (
    PlayerDB,
    SettingsData,
    TournamentData,
    format_date_extended,
    split_history_entry,
    tournament_registered,
)

INIZIO = "2026-10-01T10:00:00+02:00"
FINE = "2026-10-03T18:00:00+02:00"
CRITERI = ("Vittorie", "Alto", "Scontro Diretto (Punti)", "Punti Totali")

finestre_vere = [
    pytest.mark.finestre_vere,
    pytest.mark.skipif(sys.platform != "win32", reason="il desktop nascosto esiste solo in Windows"),
]


def _torneo(base, concluso=True):
    """Tre discepoli, tre partite: Marco batte tutti, Anna batte Luca."""
    t = TournamentData(base_dir=base)
    t.title = "Torneo di prova"
    t.start_date = INIZIO
    t.end_date = FINE if concluso else ""
    t.players = {"Marco": [6, 2, 0, 0], "Anna": [3, 1, 0, 1], "Luca": [0, 0, 0, 2]}
    t.played_matches = {
        1: ["Marco", "Anna", "1", 3, 3, 0],
        2: ["Marco", "Luca", "1", 3, 3, 0],
        3: ["Anna", "Luca", "1", 3, 3, 0],
    }
    if not concluso:
        t.unplayed_matches = {4: ["Luca", "Marco"]}
    return t


def test_concluso_e_il_segno_di_finalizzazione(tmp_path):
    base = str(tmp_path)
    t = _torneo(base)
    assert t.concluso() and t.finalized is False
    assert not _torneo(base, concluso=False).concluso()
    t.finalized = True
    t.save()
    riletto = TournamentData(base_dir=base)
    assert riletto.load() and riletto.finalized is True
    # Un file scritto fino alla 2.15.0 non ha il segno: vale falso.
    with open(t.filename, encoding="utf-8") as f:
        dati = json.load(f)
    del dati["finalized"]
    with open(t.filename, "w", encoding="utf-8") as f:
        json.dump(dati, f)
    vecchio = TournamentData(base_dir=base)
    assert vecchio.load() and vecchio.finalized is False


def test_un_torneo_premiato_prima_del_segno_si_riconosce_dallo_storico():
    inizio, fine = format_date_extended(INIZIO), format_date_extended(FINE)
    players = {
        "Marco": {
            "medals": {"oro": 1, "argento": 0, "bronzo": 0, "legno": 0},
            "history": [f"1° in Torneo di prova - {inizio} - {fine}"],
            "placements_sum": 1,
        }
    }
    assert tournament_registered(players, "Torneo di prova", INIZIO)
    assert tournament_registered(players, " Torneo di prova ", INIZIO)
    assert tournament_registered(players, "Torneo di prova", inizio)
    assert not tournament_registered(players, "Altro torneo", INIZIO)
    assert not tournament_registered(players, "Torneo di prova", "2026-11-01T10:00:00+01:00")
    assert not tournament_registered({}, "Torneo di prova", INIZIO)
    assert not tournament_registered(players, "", INIZIO)


def _finestre_vere(funzione):
    """I segni delle prove che aprono finestre vere, uno a uno: le prove sui
    soli dati, qui sopra, girano dovunque."""
    for marca in finestre_vere:
        funzione = marca(funzione)
    return funzione


@_finestre_vere
def test_la_finestra_di_finalizzazione_parte_dai_criteri_del_torneo(tmp_path):
    import wx

    from dialogs import FinalizeTournamentDialog

    app = wx.App(False)
    base = str(tmp_path)
    t = _torneo(base)
    t.main_criterion = "Punti"
    t.score_direction = "Basso"
    t.tiebreaker_1 = "Nessuno"
    t.tiebreaker_2 = "Vittorie Totali"
    dlg = FinalizeTournamentDialog(None, t, SettingsData(base_dir=base))
    assert dlg.cb_main.GetStringSelection() == "Punti"
    assert dlg.cb_score_dir.GetSelection() == 1
    assert dlg.cb_tie1.GetStringSelection() == "Nessuno"
    assert dlg.cb_tie2.GetStringSelection() == "Vittorie Totali"
    assert dlg.criteri() == ("Punti", "Basso", "Nessuno", "Vittorie Totali")
    assert "tutte le sfide sono concluse" in dlg.txt_msg.GetValue()
    assert dlg.btn_cancel.GetLabel() == "Non ora, rimando"
    # Esc vale Non ora: nessuna scelta.
    wx.CallLater(300, lambda: dlg.EndModal(dlg.GetEscapeId()))
    esito = dlg.ShowModal()
    scelta = dlg.choice
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_CANCEL and scelta is None


@_finestre_vere
def test_tutti_in_massa_e_uno_per_uno(tmp_path):
    import wx

    from dialogs import FinalizeTournamentDialog

    app = wx.App(False)
    base = str(tmp_path)
    t = _torneo(base)
    settings = SettingsData(base_dir=base)
    for pulsante, attesa in (("btn_mass", "mass"), ("btn_individual", "individual")):
        dlg = FinalizeTournamentDialog(None, t, settings)
        bottone = getattr(dlg, pulsante)
        wx.CallLater(
            300,
            lambda b=bottone: wx.PostEvent(b, wx.CommandEvent(wx.wxEVT_BUTTON, b.GetId())),
        )
        esito = dlg.ShowModal()
        scelta, criteri = dlg.choice, dlg.criteri()
        dlg.Destroy()
        assert esito == wx.ID_OK and scelta == attesa
        assert criteri == CRITERI
    app.Destroy()


class _FinestraFinta:
    """La finestra di finalizzazione che risponde da sola: si usa al posto
    della classe, e la costruzione restituisce sempre lo stesso oggetto."""

    def __init__(self, esito, scelta, criteri=CRITERI):
        self._esito = esito
        self.choice = scelta
        self._criteri = criteri
        self.aperta = 0

    def __call__(self, parent, tourney, settings):
        self.aperta += 1
        return self

    def ShowModal(self):
        return self._esito

    def criteri(self):
        return self._criteri

    def Destroy(self):
        pass


def _prepara(monkeypatch, finta, revisione=None):
    """Mette la finestra finta al posto di quella vera, raccoglie i
    messaggi di wx invece di aprirli, e se c'e' sostituisce anche la
    finestra della revisione uno per uno."""
    import wx

    import premiazione

    monkeypatch.setattr(premiazione, "FinalizeTournamentDialog", finta)
    messaggi = []

    def messaggio(testo, titolo="", *a, **k):
        messaggi.append((titolo, testo))
        return wx.OK

    monkeypatch.setattr(premiazione.wx, "MessageBox", messaggio)
    if revisione is not None:
        monkeypatch.setattr(premiazione, "SinglePlayerReviewDialog", revisione)
    return messaggi


def _posizioni(db):
    return {
        nome: split_history_entry(dati["history"][0])[0]
        for nome, dati in db.players.items()
    }


@_finestre_vere
def test_tutti_in_massa_incide_e_segna_il_torneo(monkeypatch, tmp_path):
    import wx

    from premiazione import finalizza_torneo

    app = wx.App(False)
    base = str(tmp_path)
    t = _torneo(base)
    t.save()
    db = PlayerDB(base_dir=base)
    messaggi = _prepara(monkeypatch, _FinestraFinta(wx.ID_OK, "mass"))
    frame = wx.Frame(None)
    esito = finalizza_torneo(frame, t, SettingsData(base_dir=base), db)
    frame.Destroy()
    app.Destroy()
    assert esito is True
    assert t.finalized is True
    riletto = TournamentData(base_dir=base)
    assert riletto.load() and riletto.finalized is True
    assert (riletto.main_criterion, riletto.score_direction, riletto.tiebreaker_1, riletto.tiebreaker_2) == CRITERI
    assert _posizioni(db) == {"Marco": 1, "Anna": 2, "Luca": 3}
    assert db.players["Marco"]["medals"]["oro"] == 1
    assert (tmp_path / "Dadillo_players.json").exists()
    assert tournament_registered(db.players, t.title, t.start_date)
    assert messaggi[-1][0] == "Premiazione e Registrazione Conclusa"
    assert "Discepoli aggiornati: 3." in messaggi[-1][1]
    assert "Saltati" not in messaggi[-1][1]


@_finestre_vere
def test_rimandare_non_cambia_niente(monkeypatch, tmp_path):
    import wx

    from premiazione import finalizza_torneo

    app = wx.App(False)
    base = str(tmp_path)
    t = _torneo(base)
    db = PlayerDB(base_dir=base)
    finta = _FinestraFinta(wx.ID_CANCEL, None)
    messaggi = _prepara(monkeypatch, finta)
    frame = wx.Frame(None)
    esito = finalizza_torneo(frame, t, SettingsData(base_dir=base), db)
    frame.Destroy()
    app.Destroy()
    assert esito is False and finta.aperta == 1
    assert t.finalized is False
    assert db.players == {}
    assert messaggi == []
    assert not (tmp_path / "Dadillo_players.json").exists()


class _RevisioneFinta:
    """La finestra della revisione uno per uno: salta Anna, conferma gli altri."""

    def __init__(self, parent, player_name, **dati):
        self.nome = player_name
        self.dati = dati

    def ShowModal(self):
        import wx

        return wx.ID_CANCEL if self.nome == "Anna" else wx.ID_OK

    def Destroy(self):
        pass


@_finestre_vere
def test_uno_per_uno_puo_saltare_un_discepolo(monkeypatch, tmp_path):
    import wx

    from premiazione import finalizza_torneo

    app = wx.App(False)
    base = str(tmp_path)
    t = _torneo(base)
    t.save()
    db = PlayerDB(base_dir=base)
    messaggi = _prepara(monkeypatch, _FinestraFinta(wx.ID_OK, "individual"), _RevisioneFinta)
    frame = wx.Frame(None)
    esito = finalizza_torneo(frame, t, SettingsData(base_dir=base), db)
    frame.Destroy()
    app.Destroy()
    assert esito is True and t.finalized is True
    assert _posizioni(db) == {"Marco": 1, "Luca": 3}
    assert "Discepoli aggiornati: 2." in messaggi[-1][1]
    assert "Saltati o già registrati: 1." in messaggi[-1][1]


@_finestre_vere
def test_la_classifica_finale_dice_che_il_torneo_e_finalizzato(tmp_path):
    import wx

    from standings import StandingsPanel

    app = wx.App(False)
    base = str(tmp_path)
    settings = SettingsData(base_dir=base)

    def etichette(finalizzato):
        t = _torneo(base)
        t.finalized = finalizzato
        frame = wx.Frame(None)
        panel = StandingsPanel(frame, t, settings)
        testi = [c.GetLabel() for c in panel.GetChildren() if isinstance(c, wx.StaticText)]
        pulsanti = [c.GetLabel() for c in panel.GetChildren() if isinstance(c, wx.Button)]
        frame.Destroy()
        return testi, pulsanti

    testi, pulsanti = etichette(True)
    assert any(e.startswith("Torneo finalizzato") for e in testi)
    assert pulsanti == ["Torna alle Partite"]
    testi, pulsanti = etichette(False)
    assert not any(e.startswith("Torneo finalizzato") for e in testi)
    assert pulsanti == ["Torna alle Partite"]
    app.Destroy()
