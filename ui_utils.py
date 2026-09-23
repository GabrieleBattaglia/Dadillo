"""Utilita' condivise dalle finestre di Dadillo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from data import SaveError

# Lo stile di tutte le finestre di dialogo: dalla 2.11.2 si ridimensionano e
# si ingrandiscono a tutto schermo, come chiede chi usa i caratteri grandi.
STILE_ADATTABILE = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX

# Sotto questa misura la finestra non si stringe: oltre, ci pensano le barre.
MISURA_MINIMA = (240, 160)


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


def pannello_scorrevole(finestra):
    """Il pannello che raccoglie i controlli di una finestra e che scorre
    quando il contenuto non ci sta. Quando un controllo riceve il focus, il
    pannello scorre da se' fino a mostrarlo, quindi chi si muove col tab lo
    vede sempre. Per lo screen reader non cambia niente: e' un pannello come
    quello di prima.
    """
    return ScrolledPanel(finestra)


def adatta_finestra(finestra, pannello, misura=None):
    """Da' alla finestra la misura del suo contenuto, dentro lo schermo.
    Fino alla 2.11.1 ogni finestra aveva una misura fissa in pixel, scelta con
    i caratteri al 100 per cento: con i caratteri di Windows al 150 i controlli
    crescevano e gli ultimi, spesso proprio il campo da compilare o i
    pulsanti, finivano fuori, in una finestra che non si poteva ne' allargare
    ne' scorrere. Adesso la misura la decide il contenuto; misura, espressa in
    pixel al 100 per cento, resta come minimo, cosi' con i caratteri normali
    la finestra ha l'aspetto di sempre. Se il contenuto supera lo schermo, la
    finestra si ferma al bordo e il pannello scorre.
    Va chiamata di nuovo quando il contenuto cambia misura.
    """
    pannello.SetupScrolling(scrollToTop=False)
    larghezza, altezza = finestra.ClientToWindowSize(pannello.GetSizer().GetMinSize())
    if misura:
        voluta = finestra.FromDIP(wx.Size(misura))
        larghezza = max(larghezza, voluta.width)
        altezza = max(altezza, voluta.height)
    schermo = wx.Display.GetFromWindow(finestra.GetParent() or finestra)
    area = wx.Display(max(schermo, 0)).GetClientArea()
    if altezza > area.height:
        # La barra verticale ruba spazio in larghezza: se non glielo si
        # restituisce, compare anche quella orizzontale.
        larghezza += wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X, finestra)
    larghezza = min(larghezza, area.width)
    altezza = min(altezza, area.height)
    finestra.SetMinSize(finestra.FromDIP(wx.Size(MISURA_MINIMA)))
    finestra.SetSize(larghezza, altezza)
    finestra.CentreOnParent()
    x, y = finestra.GetPosition()
    x = min(max(x, area.x), area.x + area.width - larghezza)
    y = min(max(y, area.y), area.y + area.height - altezza)
    finestra.Move(x, y)
