"""Dadillo, L'Altare del Sacrificio. Punto di ingresso dell'applicazione.
Gestore di tornei con interfaccia wxPython, pensato per l'uso con screen reader.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import sys
import threading

import wx

from main_window import MainFrame
from version import VERSION


class App(wx.App):
    def OnInit(self):
        self.frame = MainFrame()
        return True


def check_updates_gui():
    """Controlla se esiste una versione piu' recente, ma solo per l'eseguibile.
    Il controllo su sys.frozen viene prima dell'importazione di GBUtils: da
    sorgente il programma deve partire anche dove GBUtils non e' installato.
    """
    if not getattr(sys, "frozen", False):
        return

    try:
        from GBUtils import perform_update, update_checker
    except ImportError:
        # Senza GBUtils si resta senza controllo aggiornamenti, ma il programma
        # deve partire lo stesso: l'eseguibile non ha una console dove mostrare
        # l'errore, quindi un'eccezione qui sarebbe una chiusura muta.
        return

    def _update_task():
        api_url = (
            "https://api.github.com/repos/GabrieleBattaglia/dadillo/releases/latest"
        )
        has_update, new_ver, dl_url, _changelog = update_checker(VERSION, api_url)
        if has_update:
            wx.CallAfter(_show_prompt, new_ver, dl_url)

    def _show_prompt(new_ver, dl_url):
        if dl_url:
            msg = (
                f"E' disponibile la versione {new_ver}.\n"
                f"Tu hai la {VERSION}.\n"
                "Vuoi scaricarla e installarla ora?"
            )
            dlg = wx.MessageDialog(
                None, msg, "Aggiornamento Disponibile", wx.YES_NO | wx.ICON_INFORMATION
            )
            if dlg.ShowModal() == wx.ID_YES:
                if perform_update(dl_url, "Dadillo"):
                    dlg.Destroy()
                    wx.GetApp().ExitMainLoop()
                    sys.exit(0)
                else:
                    wx.MessageBox(
                        "Si è verificato un errore durante la preparazione dell'aggiornamento.",
                        "Errore",
                        wx.OK | wx.ICON_ERROR,
                    )
            dlg.Destroy()
        else:
            msg = (
                f"E' disponibile la versione {new_ver},\n"
                "ma i file di installazione non sono\n"
                "ancora pronti per il download.\n"
                "Riprova più tardi."
            )
            wx.MessageBox(msg, "Aggiornamento Disponibile", wx.OK | wx.ICON_INFORMATION)

    threading.Thread(target=_update_task, daemon=True).start()


if __name__ == "__main__":
    app = App()
    check_updates_gui()
    try:
        app.MainLoop()
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit(0)
