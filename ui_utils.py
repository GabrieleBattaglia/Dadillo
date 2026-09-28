"""Utilita' condivise dalle finestre di Dadillo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5.5, UltraCode.
Fino alla 2.11.2 qui stavano anche le funzioni che danno alle finestre la
misura dal contenuto: dalla 2.11.4 vengono da GBwx di GBUtils, dove sono
passate per servire a tutte le applicazioni con le finestre.
"""

import wx

from data import SaveError


def save_or_warn(saver, parent=None, titolo="Salvataggio non riuscito"):
    """Esegue un salvataggio e avvisa l'utente con un messaggio parlante se fallisce.
    saver e' una funzione senza argomenti, per esempio tourney.save.
    Restituisce True se il salvataggio e' andato a buon fine, False altrimenti.
    """
    try:
        saver()
        return True
    except SaveError as e:
        wx.MessageBox(str(e), titolo, wx.OK | wx.ICON_ERROR, parent)
        return False
