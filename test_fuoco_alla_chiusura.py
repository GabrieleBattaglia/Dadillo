"""Il fuoco torna dov'era quando una finestra di dialogo si chiude, dalla
2.11.4 (issue 11).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5.5, UltraCode.

Fino alla 2.11.2, annullata una finestra di dialogo, il fuoco restava sulla
cornice della finestra principale, dove NVDA legge soltanto il titolo. I
dialoghi tengono i controlli nel pannello di pannello_scorrevole, e alla loro
distruzione il fuoco passava dal controllo al pannello e dal pannello al
dialogo: la finestra principale, riattivata con il fuoco sul dialogo a meta'
distruzione, credeva di averlo gia' e non lo rimetteva. Lo corregge GBwx
1.0.1, da cui Dadillo prende pannello_scorrevole dalla 2.11.4.
Le finestre sono vere e si aprono davvero, sul desktop nascosto di
conftest.py, dove il fuoco e l'attivazione funzionano come sullo schermo ma
nessuno li vede. La finestra principale e' finta ma costruita come quella di
Dadillo, con la lista delle partite dentro pannello_scorrevole: la vera
leggerebbe e scriverebbe i file del torneo. ESC arriva come dalla tastiera,
passando dal gancio della tastiera di wx, imitato con wxEVT_CHAR_HOOK.
"""

import sys
import time

import pytest

pytestmark = [
    pytest.mark.finestre_vere,
    pytest.mark.skipif(sys.platform != "win32", reason="il desktop nascosto esiste solo in Windows"),
]

# Oltre questo tempo una finestra che non si e' chiusa viene chiusa lo
# stesso, e la prova fallisce: meglio un fallimento che una suite ferma.
RETE_DI_SICUREZZA_MS = 5000


def _attendi(condizione, secondi=2.0):
    """Lascia lavorare il ciclo degli eventi finche' la condizione e' vera,
    o finche' scade il tempo; dice se e' diventata vera."""
    import wx

    fine = time.monotonic() + secondi
    while True:
        wx.GetApp().ProcessPendingEvents()
        wx.YieldIfNeeded()
        if condizione():
            return True
        if time.monotonic() > fine:
            return False
        time.sleep(0.01)


def _descrivi(finestra):
    if finestra is None:
        return "nessun controllo"
    return f"{type(finestra).__name__} di {type(finestra.GetTopLevelParent()).__name__}"


def _esc(controllo):
    """ESC sul controllo col fuoco, come dalla tastiera: il gancio di wx lo
    fa salire fino al dialogo, che lo trasforma in Annulla."""
    import wx

    evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
    evento.SetKeyCode(wx.WXK_ESCAPE)
    evento.SetEventObject(controllo)
    evento.SetId(controllo.GetId())
    controllo.GetEventHandler().ProcessEvent(evento)


def _principale():
    """Una finestra principale come quella di Dadillo, con il fuoco sulla
    lista delle partite da giocare."""
    import wx
    from GBwx import pannello_scorrevole

    cornice = wx.Frame(None, title="Dadillo delle prove")
    pannello = pannello_scorrevole(cornice)
    filtro = wx.TextCtrl(pannello)
    lista = wx.ListBox(pannello, choices=["1: Anna contro Bruno", "2: Carla contro Dario"])
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(filtro, 0, wx.EXPAND)
    sizer.Add(lista, 1, wx.EXPAND)
    pannello.SetSizer(sizer)
    cornice.Show()
    cornice.Raise()
    lista.SetFocus()
    assert _attendi(lambda: wx.Window.FindFocus() is lista), (
        f"La lista non ha preso il fuoco: ce l'ha {_descrivi(wx.Window.FindFocus())}"
    )
    return cornice, lista


def _dialoghi():
    """I dialoghi che la finestra principale apre, con i loro argomenti."""
    from data import SettingsData
    from dialogs import (
        AddPlayerDialog,
        MatchResultDialog,
        RetirePlayerDialog,
        SettingsDialog,
    )

    return {
        "risultato": lambda genitore: MatchResultDialog(genitore, 1, "Anna", "Bruno"),
        "risultato con i punti predefiniti": lambda genitore: MatchResultDialog(
            genitore, 1, "Anna", "Bruno", use_defaults=True
        ),
        "impostazioni": lambda genitore: SettingsDialog(genitore, SettingsData()),
        "nuovo giocatore": lambda genitore: AddPlayerDialog(genitore, ["Anna", "Bruno"]),
        "ritiro": lambda genitore: RetirePlayerDialog(genitore, ["Anna", "Bruno"]),
    }


@pytest.mark.parametrize("nome", list(_dialoghi()))
@pytest.mark.parametrize("chiusura", ["esc", "annulla"])
def test_il_fuoco_torna_sulla_lista(nome, chiusura):
    import wx

    app = wx.App(False)
    cornice, lista = _principale()
    dlg = _dialoghi()[nome](cornice)
    stato = {"fuoco_dentro": None, "rete": False}

    def chiudi():
        fuoco = wx.Window.FindFocus()
        stato["fuoco_dentro"] = fuoco is not None and fuoco.GetTopLevelParent() is dlg
        if chiusura == "esc" and fuoco is not None:
            _esc(fuoco)
        else:
            dlg.EndModal(wx.ID_CANCEL)

    def rete():
        if dlg.IsModal():
            stato["rete"] = True
            dlg.EndModal(wx.ID_CANCEL)

    wx.CallLater(300, chiudi)
    sicurezza = wx.CallLater(RETE_DI_SICUREZZA_MS, rete)
    esito = dlg.ShowModal()
    sicurezza.Stop()
    dlg.Destroy()
    try:
        assert not stato["rete"], "Il dialogo non si e' chiuso da se': l'ha chiuso la rete di sicurezza."
        assert esito == wx.ID_CANCEL
        assert stato["fuoco_dentro"], "Alla chiusura il fuoco non era dentro il dialogo: la prova non prova niente."
        tornato = _attendi(lambda: wx.Window.FindFocus() is lista)
        assert tornato, f"Chiuso il dialogo, il fuoco e' su {_descrivi(wx.Window.FindFocus())}, non sulla lista."
    finally:
        cornice.Destroy()
        _attendi(lambda: False, 0.05)
        app.Destroy()
