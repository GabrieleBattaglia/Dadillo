"""Dadillo, L'Altare del Sacrificio. Punto di ingresso dell'applicazione.
Gestore di tornei con interfaccia wxPython, pensato per l'uso con screen reader.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto;
controllo aggiornamenti della 2.12 di ClaudIA, Claude Opus 5.5, UltraCode.
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
    Dalla 2.12.0 la proposta riceve da GBUtils V172 il tempo massimo per
    rispondere, due minuti, e allo scadere la finestra si chiude come non
    adesso. Dalla 2.12.1 anche avvisa aspetta che l'utente chiuda il
    messaggio: GBUtils dice che il programma si chiude prima di avviare lo
    script che lo sostituisce, e l'attesa dell'OK non deve consumare i 30
    secondi entro cui il programma deve uscire. Fino alla 2.11.5 il
    messaggio si apriva e avvisa tornava subito: chi premeva OK dopo 30
    secondi si ritrovava il programma chiuso e l'aggiornamento non
    applicato (issue 13).
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
    # L'avviso dello scaricamento: nasce quando l'utente accetta e lo rilascia
    # l'esito, che arriva sempre. Sta in una lista perche' chi lo apre e chi lo
    # chiude sono due momenti diversi.
    avviso_scarico = []

    def finestra_padre():
        app = wx.GetApp()
        return getattr(app, "frame", None) if app else None

    def proponi(versione_attuale, versione_nuova, note, attesa=None):
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

                dlg = UpdateDialog(
                    finestra_padre(), versione_attuale, versione_nuova, note, attesa=attesa
                )
                scelta = dlg.ShowModal()
                dlg.Destroy()
                if scelta != wx.ID_YES:
                    return
                risposta.append(True)
                avviso_scarico.append(
                    wx.BusyInfo("Scarico l'aggiornamento, aspetta.", parent=finestra_padre())
                )
            finally:
                risposto.set()

        wx.CallAfter(nella_finestra)
        risposto.wait()
        return bool(risposta)

    def mostra_esito(testo, letto):
        try:
            # Svuotare la lista rilascia l'avviso e lo fa sparire; se non era
            # aperto, non cambia niente.
            avviso_scarico.clear()
            wx.MessageBox(testo, "Aggiornamento", wx.OK | wx.ICON_INFORMATION, finestra_padre())
        finally:
            letto.set()

    def avvisa(testo):
        # Come proponi: il messaggio nasce sul thread della finestra, e qui si
        # resta fermi finche' l'utente non lo chiude.
        letto = threading.Event()
        wx.CallAfter(mostra_esito, testo, letto)
        letto.wait()

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
