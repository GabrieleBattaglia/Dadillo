"""Utilita' condivise dalle finestre di Dadillo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
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
