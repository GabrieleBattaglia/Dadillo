"""L'unione manuale, dalla 2.17.0: un torneo giocato altrove inciso nella
Hall of Fame con titolo, date e classifica, senza il suo file (richiesta di
Gabriele del 18 novembre 2026).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Le finestre vere si aprono sul desktop nascosto di conftest.py; dove serve
una risposta sono sostituite da copie finte, e i messaggi di wx si
raccolgono invece di aprirsi. L'archivio sta in una cartella di prova:
niente di vero si legge o si scrive accanto al programma.
"""

import copy
import sys

import pytest

from data import (
    PlayerDB,
    SaveError,
    fields_to_timestamp,
    split_history_entry,
    tournament_registered,
)

TITOLO = "Torneo di Carol"
INIZIO = fields_to_timestamp("7/11/2026", "")
FINE = fields_to_timestamp("14/11/2026", "")
CLASSIFICA = ["Carol", "Peppe", "Selene157", "Gas"]
VUOTO = {"oro": 0, "argento": 0, "bronzo": 0, "legno": 0}

finestre_vere = [
    pytest.mark.finestre_vere,
    pytest.mark.skipif(sys.platform != "win32", reason="il desktop nascosto esiste solo in Windows"),
]


def _finestre_vere(funzione):
    """I segni delle prove che aprono finestre vere, uno a uno: le prove sui
    soli dati girano dovunque."""
    for marca in finestre_vere:
        funzione = marca(funzione)
    return funzione


def _archivio(base):
    """Un archivio con tre discepoli, uno dei quali ha gia' un torneo."""
    db = PlayerDB(base_dir=base)
    for nome in ("Peppe", "Gas", "Anny.88"):
        db.players[nome] = {"medals": dict(VUOTO), "history": [], "placements_sum": 0}
    db.players["Peppe"]["history"].append(
        "1° in Farkle Bonus - martedì 17 marzo 2026 - lunedì 20 aprile 2026"
    )
    db.recalculate_player_stats("Peppe")
    return db


def _posizioni(db, titolo=TITOLO):
    """Le posizioni che lo storico dice per il torneo, discepolo per discepolo."""
    posizioni = {}
    for nome, dati in db.players.items():
        for voce in dati["history"]:
            pos, voce_titolo, _, _ = split_history_entry(voce)
            if voce_titolo == titolo:
                posizioni[nome] = pos
    return posizioni


def test_registra_classifica_incide_posizioni_medaglie_e_conti(tmp_path):
    from unione_manuale import registra_classifica

    db = _archivio(str(tmp_path))
    conti = registra_classifica(db, TITOLO, INIZIO, FINE, CLASSIFICA)
    assert (conti.aggiornati, conti.nuovi, conti.gia_registrati) == (4, 2, 0)
    assert _posizioni(db) == {"Carol": 1, "Peppe": 2, "Selene157": 3, "Gas": 4}
    assert db.players["Carol"]["medals"] == {"oro": 1, "argento": 0, "bronzo": 0, "legno": 0}
    assert db.players["Peppe"]["medals"] == {"oro": 1, "argento": 1, "bronzo": 0, "legno": 0}
    assert db.players["Gas"]["medals"]["legno"] == 1
    assert db.players["Peppe"]["placements_sum"] == 3
    assert db.players["Selene157"]["history"] == [
        f"3° in {TITOLO} - sabato 7 novembre 2026 - sabato 14 novembre 2026"
    ]
    assert tournament_registered(db.players, TITOLO, INIZIO)
    # Chi non ha giocato resta com'era, e non si salva: lo fa chi chiama.
    assert db.players["Anny.88"]["history"] == []
    assert not (tmp_path / "Dadillo_players.json").exists()
    # Una seconda volta, con un nome in piu': solo lui prende la voce.
    conti = registra_classifica(db, TITOLO, INIZIO, FINE, [*CLASSIFICA, "Nuovo"])
    assert (conti.aggiornati, conti.nuovi, conti.gia_registrati) == (1, 1, 4)
    assert _posizioni(db)["Nuovo"] == 5
    assert len(db.players["Carol"]["history"]) == 1


def _raccogli_messaggi(monkeypatch, risposta=None):
    """I messaggi di wx si raccolgono invece di aprirsi, con la risposta data."""
    import wx

    messaggi = []

    def messaggio(testo, titolo="", *a, **k):
        messaggi.append((titolo, testo))
        return wx.OK if risposta is None else risposta

    monkeypatch.setattr(wx, "MessageBox", messaggio)
    return messaggi


def _premi(bottone):
    """Preme un pulsante dalla coda degli eventi, a finestra aperta."""
    import wx

    wx.CallLater(
        300,
        lambda: wx.PostEvent(bottone, wx.CommandEvent(wx.wxEVT_BUTTON, bottone.GetId())),
    )


@_finestre_vere
def test_la_finestra_del_torneo_controlla_titolo_e_date(monkeypatch):
    import wx

    from dialogs import ManualUnionDialog

    app = wx.App(False)
    messaggi = _raccogli_messaggi(monkeypatch)
    dlg = ManualUnionDialog(None)
    assert dlg._leggi() is None and messaggi[-1][0] == "Titolo mancante"
    dlg.txt_titolo.SetValue(f" {TITOLO} ")
    assert dlg._leggi() is None and messaggi[-1][0] == "Data non valida"
    assert "inizio" in messaggi[-1][1]
    dlg.txt_inizio.SetValue("7/11/2026")
    dlg.txt_fine.SetValue("31/2/2026")
    assert dlg._leggi() is None and "fine" in messaggi[-1][1]
    dlg.txt_fine.SetValue("6/11/2026")
    assert dlg._leggi() is None and messaggi[-1][0] == "Date incoerenti"
    dlg.txt_fine.SetValue("14/11/2026")
    assert dlg._leggi() == (TITOLO, INIZIO, FINE)
    assert dlg.valori is None
    # Avanti chiude con i valori controllati.
    _premi(dlg.btn_ok)
    esito = dlg.ShowModal()
    valori = dlg.valori
    dlg.Destroy()
    assert esito == wx.ID_OK and valori == (TITOLO, INIZIO, FINE)
    # Riaperta con i valori, li mostra nei campi; Esc chiude senza.
    dlg = ManualUnionDialog(None, TITOLO, INIZIO, FINE)
    assert dlg.txt_titolo.GetValue() == TITOLO
    assert dlg.txt_inizio.GetValue() == "07/11/2026"
    assert dlg.txt_fine.GetValue() == "14/11/2026"
    wx.CallLater(300, lambda: dlg.EndModal(wx.ID_CANCEL))
    esito = dlg.ShowModal()
    valori = dlg.valori
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_CANCEL and valori is None


def _tasto(codice, ctrl):
    import wx

    evento = wx.KeyEvent(wx.wxEVT_KEY_DOWN)
    evento.SetKeyCode(codice)
    evento.SetControlDown(ctrl)
    return evento


def _righe(elenco):
    return [elenco.GetString(i) for i in range(elenco.GetCount())]


@_finestre_vere
def test_i_partecipanti_si_ordinano_con_ctrl_e_le_frecce(tmp_path):
    import wx

    from dialogs import ManualUnionPlayersDialog

    app = wx.App(False)
    db = _archivio(str(tmp_path))
    dlg = ManualUnionPlayersDialog(None, TITOLO, ["Carol", "Peppe", "Selene157"], db=db)
    assert dlg.GetTitle() == "Unione manuale: i partecipanti"
    assert TITOLO in dlg.lbl_msg.GetLabel()
    assert dlg.btn_ok.GetLabel() == "Inserisci torneo nello storico"
    assert _righe(dlg.list_players) == ["1° Carol", "2° Peppe", "3° Selene157"]
    # Dall'archivio restano da scegliere quelli che non partecipano ancora.
    assert _righe(dlg.list_db_players) == ["Anny.88", "Gas"]
    dlg.list_players.SetSelection(0)
    dlg.on_key_down(_tasto(wx.WXK_DOWN, True))
    assert dlg.players == ["Peppe", "Carol", "Selene157"]
    assert _righe(dlg.list_players) == ["1° Peppe", "2° Carol", "3° Selene157"]
    assert dlg.list_players.GetSelection() == 1
    dlg.on_key_down(_tasto(wx.WXK_DOWN, True))
    assert dlg.players == ["Peppe", "Selene157", "Carol"]
    assert dlg.list_players.GetSelection() == 2
    # In fondo Ctrl con Freccia giu' non fa niente; su, risale.
    dlg.on_key_down(_tasto(wx.WXK_DOWN, True))
    assert dlg.players == ["Peppe", "Selene157", "Carol"]
    assert dlg.list_players.GetSelection() == 2
    dlg.on_key_down(_tasto(wx.WXK_UP, True))
    assert dlg.players == ["Peppe", "Carol", "Selene157"]
    assert dlg.list_players.GetSelection() == 1
    # Senza Ctrl la freccia resta al controllo: l'ordine non cambia.
    dlg.on_key_down(_tasto(wx.WXK_UP, False))
    assert dlg.players == ["Peppe", "Carol", "Selene157"]
    # Canc toglie il selezionato e le posizioni di chi segue scalano.
    dlg.on_key_down(_tasto(wx.WXK_DELETE, False))
    assert dlg.players == ["Peppe", "Selene157"]
    assert _righe(dlg.list_players) == ["1° Peppe", "2° Selene157"]
    assert dlg.list_players.GetSelection() == 1
    # Dall'archivio e dal campo del nome si va in coda, con la posizione.
    dlg.add_from_db(1)
    assert dlg.players == ["Peppe", "Selene157", "Gas"]
    assert _righe(dlg.list_players)[-1] == "3° Gas"
    dlg.txt_player.SetValue("Dj Dany")
    dlg.on_add_player(None)
    assert dlg.players == ["Peppe", "Selene157", "Gas", "Dj Dany"]
    assert _righe(dlg.list_players)[-1] == "4° Dj Dany"
    # Il pulsante chiude con OK e i partecipanti restano nell'ordine dato.
    _premi(dlg.btn_ok)
    esito = dlg.ShowModal()
    partecipanti = list(dlg.players)
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_OK and partecipanti == ["Peppe", "Selene157", "Gas", "Dj Dany"]


@_finestre_vere
def test_la_scelta_dei_giocatori_del_torneo_nuovo_resta_alfabetica(tmp_path):
    import wx

    from dialogs import SetupPlayersDialog

    app = wx.App(False)
    db = _archivio(str(tmp_path))
    dlg = SetupPlayersDialog(None, ["Zoe", "Anna"], db=db)
    assert dlg.GetTitle() == "Raduna i Tuoi Discepoli"
    assert dlg.btn_ok.GetLabel() == "Tutti pronti al massacro!"
    assert _righe(dlg.list_players) == ["Anna", "Zoe"]
    # Qui Ctrl con le frecce non sposta niente.
    dlg.list_players.SetSelection(0)
    dlg.on_key_down(_tasto(wx.WXK_DOWN, True))
    assert dlg.players == ["Zoe", "Anna"]
    # Canc toglie la riga selezionata, Anna, non la prima inserita.
    dlg.on_key_down(_tasto(wx.WXK_DELETE, False))
    assert dlg.players == ["Zoe"]
    dlg.add_from_db(0)
    assert dlg.players == ["Zoe", "Anny.88"]
    assert _righe(dlg.list_players) == ["Anny.88", "Zoe"]
    dlg.Destroy()
    app.Destroy()


class _TorneoFinto:
    """La finestra di titolo e date che risponde da sola: ogni apertura
    consuma un esito e ricorda i valori con cui e' stata aperta."""

    def __init__(self, esiti, valori, id_ok):
        self.esiti = list(esiti)
        self._valori = valori
        self._id_ok = id_ok
        self.aperture = []

    def __call__(self, parent, titolo="", inizio="", fine=""):
        self.aperture.append((titolo, inizio, fine))
        self.esito = self.esiti.pop(0)
        self.valori = self._valori if self.esito == self._id_ok else None
        return self

    def ShowModal(self):
        return self.esito

    def Destroy(self):
        pass


class _PartecipantiFinti:
    """La finestra dei partecipanti che risponde da sola, con la classifica
    data, e ricorda i nomi con cui e' stata aperta."""

    def __init__(self, esiti, players):
        self.esiti = list(esiti)
        self.players = list(players)
        self.aperture = []

    def __call__(self, parent, titolo, existing_players=None, db=None):
        self.aperture.append((titolo, list(existing_players or [])))
        self.esito = self.esiti.pop(0)
        return self

    def ShowModal(self):
        return self.esito

    def Destroy(self):
        pass


def _prepara(monkeypatch, torneo, partecipanti, risposta=None):
    """Le due finestre finte al posto di quelle vere, e i messaggi raccolti."""
    import unione_manuale

    monkeypatch.setattr(unione_manuale, "ManualUnionDialog", torneo)
    monkeypatch.setattr(unione_manuale, "ManualUnionPlayersDialog", partecipanti)
    return _raccogli_messaggi(monkeypatch, risposta)


@_finestre_vere
def test_unione_manuale_incide_salva_e_annuncia(monkeypatch, tmp_path):
    import wx

    from unione_manuale import unione_manuale

    app = wx.App(False)
    db = _archivio(str(tmp_path))
    torneo = _TorneoFinto([wx.ID_OK], (TITOLO, INIZIO, FINE), wx.ID_OK)
    partecipanti = _PartecipantiFinti([wx.ID_OK], CLASSIFICA)
    messaggi = _prepara(monkeypatch, torneo, partecipanti)
    frame = wx.Frame(None)
    esito = unione_manuale(frame, db)
    frame.Destroy()
    app.Destroy()
    assert esito is True
    assert torneo.aperture == [("", "", "")]
    assert partecipanti.aperture == [(TITOLO, [])]
    assert _posizioni(db) == {"Carol": 1, "Peppe": 2, "Selene157": 3, "Gas": 4}
    riletto = PlayerDB(base_dir=str(tmp_path))
    assert _posizioni(riletto) == _posizioni(db)
    testo = (tmp_path / "Giocatori.txt").read_text(encoding="utf-8")
    assert f"1° in {TITOLO} - sabato 7 novembre 2026 - sabato 14 novembre 2026" in testo
    assert messaggi[-1][0] == "Unione manuale conclusa"
    assert "con 4 partecipanti" in messaggi[-1][1]
    assert "Oro a Carol, argento a Peppe, bronzo a Selene157, legno a Gas." in messaggi[-1][1]
    assert "Discepoli aggiornati: 4." in messaggi[-1][1]
    assert "Nuovi in archivio: 2." in messaggi[-1][1]
    assert "Avevano già" not in messaggi[-1][1]


@_finestre_vere
def test_un_torneo_gia_in_archivio_chiede_prima(monkeypatch, tmp_path):
    import wx

    from unione_manuale import registra_classifica, unione_manuale

    app = wx.App(False)
    db = _archivio(str(tmp_path))
    registra_classifica(db, TITOLO, INIZIO, FINE, CLASSIFICA)
    db.save()
    prima = copy.deepcopy(db.players)
    # Con un no si torna alla prima finestra, con titolo e date gia' scritti.
    torneo = _TorneoFinto([wx.ID_OK, wx.ID_CANCEL], (TITOLO, INIZIO, FINE), wx.ID_OK)
    partecipanti = _PartecipantiFinti([wx.ID_OK], [*CLASSIFICA, "Nuovo"])
    messaggi = _prepara(monkeypatch, torneo, partecipanti, risposta=wx.NO)
    frame = wx.Frame(None)
    esito = unione_manuale(frame, db)
    assert esito is False
    assert [titolo for titolo, _ in messaggi] == ["Torneo già in archivio"]
    assert "iniziato sabato 7 novembre 2026" in messaggi[0][1]
    assert torneo.aperture == [("", "", ""), (TITOLO, INIZIO, FINE)]
    assert db.players == prima
    # Con un si' entra solo chi manca.
    torneo = _TorneoFinto([wx.ID_OK], (TITOLO, INIZIO, FINE), wx.ID_OK)
    partecipanti = _PartecipantiFinti([wx.ID_OK], [*CLASSIFICA, "Nuovo"])
    messaggi = _prepara(monkeypatch, torneo, partecipanti, risposta=wx.YES)
    esito = unione_manuale(frame, db)
    frame.Destroy()
    app.Destroy()
    assert esito is True
    assert _posizioni(db)["Nuovo"] == 5
    assert len(db.players["Carol"]["history"]) == 1
    assert [titolo for titolo, _ in messaggi] == ["Torneo già in archivio", "Unione manuale conclusa"]
    assert "Discepoli aggiornati: 1." in messaggi[-1][1]
    assert "Avevano già questo torneo: 4." in messaggi[-1][1]


@_finestre_vere
def test_tornare_a_titolo_e_date_conserva_i_partecipanti(monkeypatch, tmp_path):
    import wx

    from unione_manuale import unione_manuale

    app = wx.App(False)
    db = _archivio(str(tmp_path))
    torneo = _TorneoFinto([wx.ID_OK, wx.ID_OK, wx.ID_CANCEL], (TITOLO, INIZIO, FINE), wx.ID_OK)
    partecipanti = _PartecipantiFinti([wx.ID_CANCEL, wx.ID_CANCEL], ["Carol", "Peppe"])
    messaggi = _prepara(monkeypatch, torneo, partecipanti)
    frame = wx.Frame(None)
    esito = unione_manuale(frame, db)
    frame.Destroy()
    app.Destroy()
    assert esito is False and messaggi == []
    assert torneo.aperture == [("", "", ""), (TITOLO, INIZIO, FINE), (TITOLO, INIZIO, FINE)]
    assert partecipanti.aperture == [(TITOLO, []), (TITOLO, ["Carol", "Peppe"])]
    assert _posizioni(db) == {}
    assert not (tmp_path / "Dadillo_players.json").exists()


@_finestre_vere
def test_se_l_archivio_non_si_salva_niente_resta_cambiato(monkeypatch, tmp_path):
    import wx

    from unione_manuale import unione_manuale

    app = wx.App(False)
    db = _archivio(str(tmp_path))
    prima = copy.deepcopy(db.players)

    def salvataggio_rotto():
        raise SaveError(db.filename, OSError("disco pieno"))

    monkeypatch.setattr(db, "save", salvataggio_rotto)
    torneo = _TorneoFinto([wx.ID_OK], (TITOLO, INIZIO, FINE), wx.ID_OK)
    partecipanti = _PartecipantiFinti([wx.ID_OK], CLASSIFICA)
    messaggi = _prepara(monkeypatch, torneo, partecipanti)
    frame = wx.Frame(None)
    esito = unione_manuale(frame, db)
    frame.Destroy()
    app.Destroy()
    assert esito is False
    assert db.players == prima
    assert [titolo for titolo, _ in messaggi] == [
        "Salvataggio non riuscito",
        "Unione manuale non riuscita",
    ]


@_finestre_vere
def test_la_voce_del_menu_sta_sotto_unisci_database_giocatori(monkeypatch):
    import wx

    import main_window
    from main_window import MainFrame

    app = wx.App(False)
    # La sola barra dei menu: la finestra intera leggerebbe gli archivi veri
    # accanto al programma.
    frame = MainFrame.__new__(MainFrame)
    wx.Frame.__init__(frame, None)
    frame.create_menu()
    barra = frame.GetMenuBar()
    opzioni = barra.GetMenu(barra.FindMenu("Opzioni"))
    voci = {voce.GetItemLabelText(): voce.GetId() for voce in opzioni.GetMenuItems()}
    assert list(voci)[-2:] == ["Unisci Database Giocatori", "Unione manuale"]
    # La voce arriva all'unione manuale, con l'archivio della finestra.
    chiamate = []
    monkeypatch.setattr(main_window, "unione_manuale", lambda *a: chiamate.append(a))
    frame.player_db = archivio = object()
    frame.ProcessEvent(wx.CommandEvent(wx.wxEVT_MENU, voci["Unione manuale"]))
    frame.Destroy()
    app.Destroy()
    assert chiamate == [(frame, archivio)]
