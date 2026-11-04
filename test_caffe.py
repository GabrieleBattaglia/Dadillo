"""La finestra Offrimi un caffe', dalla 2.14.0 (issue 14).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

La finestra si apre davvero sul desktop nascosto di conftest.py. Il browser
non si apre mai: webbrowser.open viene sostituito, e la prova guarda solo
quale indirizzo avrebbe ricevuto.
"""

import sys

import pytest

pytestmark = [
    pytest.mark.finestre_vere,
    pytest.mark.skipif(sys.platform != "win32", reason="il desktop nascosto esiste solo in Windows"),
]

INVITO = "Se questo software ti è piaciuto, considera l'idea di offrirmi un caffè."


def test_chiudi_e_il_predefinito_e_esc_chiude():
    import wx

    from dialogs import DonationDialog

    app = wx.App(False)
    dlg = DonationDialog(None, INVITO)
    assert dlg.txt_msg.GetValue() == INVITO
    assert dlg.GetEscapeId() == wx.ID_NO
    assert dlg.btn_chiudi.GetLabel() == "&Chiudi"
    assert dlg.btn_dona.GetLabel() == "&Dona con PayPal"
    # Esc, come arriva dalla finestra: la via d'uscita che vale no.
    wx.CallLater(300, lambda: dlg.EndModal(dlg.GetEscapeId()))
    esito = dlg.ShowModal()
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_NO


def test_dona_apre_paypal_e_chiude(monkeypatch):
    import webbrowser

    import wx

    from dialogs import INDIRIZZO_PAYPAL, DonationDialog

    aperti = []
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: aperti.append(url) or True)
    app = wx.App(False)
    dlg = DonationDialog(None, INVITO)
    wx.CallLater(300, lambda: wx.PostEvent(dlg.btn_dona, wx.CommandEvent(wx.wxEVT_BUTTON, dlg.btn_dona.GetId())))
    esito = dlg.ShowModal()
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_YES
    assert aperti == [INDIRIZZO_PAYPAL]
    assert INDIRIZZO_PAYPAL == "https://paypal.me/GabrieleBattaglia780"


def test_un_browser_che_non_parte_non_tiene_aperto_l_invito(monkeypatch):
    import webbrowser

    import wx

    from dialogs import DonationDialog

    def rotto(url, *a, **k):
        raise OSError("nessun browser")

    monkeypatch.setattr(webbrowser, "open", rotto)
    app = wx.App(False)
    dlg = DonationDialog(None, INVITO)
    wx.CallLater(300, lambda: wx.PostEvent(dlg.btn_dona, wx.CommandEvent(wx.wxEVT_BUTTON, dlg.btn_dona.GetId())))
    esito = dlg.ShowModal()
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_YES


def test_invio_nel_testo_chiude_ma_non_subito_dopo_l_apertura():
    import wx

    from dialogs import GRAZIA_INVIO, DonationDialog, premuto_invio

    app = wx.App(False)
    dlg = DonationDialog(None, INVITO)

    def invio():
        evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
        evento.SetKeyCode(wx.WXK_RETURN)
        evento.SetEventObject(dlg.txt_msg)
        evento.SetId(dlg.txt_msg.GetId())
        return evento

    assert premuto_invio(invio())
    # Appena aperta, un Invio e' quello tenuto giu' dalla voce di menu: non chiude.
    dlg.on_char_hook(invio())
    assert not dlg.IsModal()
    # Passata la grazia, Invio nel testo chiude come Chiudi.
    dlg._aperta -= GRAZIA_INVIO + 1
    wx.CallLater(300, lambda: dlg.on_char_hook(invio()))
    esito = dlg.ShowModal()
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_NO
