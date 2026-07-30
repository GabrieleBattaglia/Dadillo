import sys

import wx
from main_window import MainFrame
from version import APP_NAME, AUTHORS, DATE, VERSION

print(f"Welcome! {APP_NAME} by {AUTHORS} - Version {VERSION} ({DATE})")


class App(wx.App):
    def OnInit(self):
        self.frame = MainFrame()
        return True


def check_updates_gui():
    import sys
    import threading

    import wx
    from version import VERSION

    from GBUtils import perform_update, update_checker

    if not getattr(sys, "frozen", False):
        return

    def _update_task():
        api_url = (
            "https://api.github.com/repos/GabrieleBattaglia/dadillo/releases/latest"
        )
        has_update, new_ver, dl_url, changelog = update_checker(VERSION, api_url)
        if has_update:
            wx.CallAfter(_show_prompt, new_ver, dl_url)

    def _show_prompt(new_ver, dl_url):
        if dl_url:
            msg = f"E' disponibile la nuova versione {new_ver}! (Attuale: {VERSION})\n\nDesideri scaricare e installare l'aggiornamento ora?"
            dlg = wx.MessageDialog(
                None, msg, "Aggiornamento Disponibile", wx.YES_NO | wx.ICON_INFORMATION
            )
            if dlg.ShowModal() == wx.ID_YES:
                if perform_update(dl_url, "Dadillo"):
                    wx.Exit()
                else:
                    wx.MessageBox(
                        "Si è verificato un errore durante la preparazione dell'aggiornamento.",
                        "Errore",
                        wx.OK | wx.ICON_ERROR,
                    )
            dlg.Destroy()
        else:
            msg = f"E' disponibile la nuova versione {new_ver}, ma i file di installazione non sono ancora pronti per il download.\n\nRiprova più tardi."
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
