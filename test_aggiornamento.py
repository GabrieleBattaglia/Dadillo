"""La finestra di aggiornamento si chiude da sola allo scadere dell'attesa,
dalla 2.12.0 (issue 13).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5.5, UltraCode.

GBUtils V172 da' alla proposta due minuti: senza risposta vale come non
adesso, e il programma prosegue. Qui l'attesa e' di pochi decimi di secondo,
e la finestra si apre davvero sul desktop nascosto di conftest.py.
"""

import sys

import pytest

pytestmark = [
    pytest.mark.finestre_vere,
    pytest.mark.skipif(sys.platform != "win32", reason="il desktop nascosto esiste solo in Windows"),
]


def test_la_finestra_si_chiude_come_non_adesso():
    import wx

    from dialogs import UpdateDialog

    app = wx.App(False)
    dlg = UpdateDialog(None, "2.11.5", "2.12.1", "Novita'.", attesa=0.3)
    # Se l'attesa non funzionasse, la rete di sicurezza chiude con un
    # risultato diverso e la prova fallisce invece di fermare la suite.
    sicurezza = wx.CallLater(5000, lambda: dlg.IsModal() and dlg.EndModal(wx.ID_CANCEL))
    esito = dlg.ShowModal()
    sicurezza.Stop()
    testo = " ".join(
        f.GetLabel() for f in dlg.GetChildren()[0].GetChildren() if isinstance(f, wx.StaticText)
    )
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_NO
    assert "la finestra si chiude da sola" in testo
    assert "te lo ripropongo al prossimo avvio" in testo


def test_senza_attesa_la_finestra_aspetta():
    import wx

    from dialogs import UpdateDialog

    app = wx.App(False)
    dlg = UpdateDialog(None, "2.11.5", "2.12.1", "Novita'.")
    wx.CallLater(800, lambda: dlg.EndModal(wx.ID_YES))
    esito = dlg.ShowModal()
    dlg.Destroy()
    app.Destroy()
    assert esito == wx.ID_YES


def test_la_durata_a_parole():
    from dialogs import durata_attesa

    assert durata_attesa(120) == "2 minuti"
    assert durata_attesa(60) == "1 minuto"
    assert durata_attesa(90) == "90 secondi"
