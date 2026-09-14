"""Dadillo, L'Altare del Sacrificio. Punto di ingresso dell'applicazione.
Gestore di tornei con interfaccia wxPython, pensato per l'uso con screen reader.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import sys
import threading

import wx

from main_window import MainFrame
from version import APP_NAME, VERSION


class App(wx.App):
    def OnInit(self):
        self.frame = MainFrame()
        return True


def check_updates_gui():
    """Controlla se esiste una versione piu' recente, ma solo per l'eseguibile.
    Il controllo su sys.frozen viene prima dell'importazione di GBUtils: da
    sorgente il programma deve partire anche dove GBUtils non e' installato.
    Dalla 2.11.0 il giro lo conduce gestisci_aggiornamento, che dalla V159 di
    GBUtils tace finche' non c'e' davvero qualcosa da aggiornare: qui restano
    la finestra e il ponte fra il thread del controllo e il thread della
    finestra, che e' l'unico che possa aprirla.
    """
    if not getattr(sys, "frozen", False):
        return

    try:
        from GBUtils import gestisci_aggiornamento
    except ImportError:
        # Senza GBUtils si resta senza controllo aggiornamenti, ma il programma
        # deve partire lo stesso: l'eseguibile non ha una console dove mostrare
        # l'errore, quindi un'eccezione qui sarebbe una chiusura muta.
        return

    api_url = "https://api.github.com/repos/GabrieleBattaglia/dadillo/releases/latest"
    # L'attesa dello scaricamento: nasce quando l'utente accetta e la rilascia
    # l'esito, che arriva sempre. Sta in una lista perche' chi la apre e chi la
    # chiude sono due momenti diversi.
    attesa = []

    def finestra_padre():
        app = wx.GetApp()
        return getattr(app, "frame", None) if app else None

    def proponi(versione_attuale, versione_nuova, note):
        """La risposta dell'utente, che gestisci_aggiornamento aspetta.
        La domanda nasce nel thread del controllo, ma la finestra vive su
        quello principale: la si porta li' con CallAfter e si resta fermi
        finche' non si sa la risposta, perche' e' lei a dire se scaricare.
        """
        risposta = []
        risposto = threading.Event()

        def nella_finestra():
            try:
                from dialogs import UpdateDialog

                dlg = UpdateDialog(finestra_padre(), versione_attuale, versione_nuova, note)
                scelta = dlg.ShowModal()
                dlg.Destroy()
                if scelta != wx.ID_YES:
                    return
                risposta.append(True)
                attesa.append(wx.BusyInfo("Scarico l'aggiornamento, aspetta.", parent=finestra_padre()))
            finally:
                risposto.set()

        wx.CallAfter(nella_finestra)
        risposto.wait()
        return bool(risposta)

    def mostra_esito(testo):
        # Svuotare la lista rilascia l'attesa e la fa sparire; se non era
        # aperta, non cambia niente.
        attesa.clear()
        wx.MessageBox(testo, "Aggiornamento", wx.OK | wx.ICON_INFORMATION, finestra_padre())

    def avvisa(testo):
        wx.CallAfter(mostra_esito, testo)

    def lavoro():
        if gestisci_aggiornamento(APP_NAME, VERSION, api_url, proponi=proponi, avvisa=avvisa):
            # ExitMainLoop e basta: il blocco finally del programma chiama poi
            # sys.exit, e chiamarlo da qui significherebbe sollevare SystemExit
            # dentro un gestore di eventi di wx.
            wx.CallAfter(wx.GetApp().ExitMainLoop)

    threading.Thread(target=lavoro, daemon=True).start()


if __name__ == "__main__":
    app = App()
    check_updates_gui()
    try:
        app.MainLoop()
    except KeyboardInterrupt:
        pass
    finally:
        sys.exit(0)
