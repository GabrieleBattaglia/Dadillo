"""L'unione manuale: un torneo giocato fuori da questo Dadillo inciso nella
Hall of Fame senza il suo file (richiesta di Gabriele del 18 novembre 2026).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Unisci Database Giocatori fonde l'archivio di un'altra copia di Dadillo, ma
serve che l'altra copia abbia finalizzato il torneo: il 5 novembre 2026 un
archivio arrivato senza il torneo dentro non aveva niente da dare. Qui si fa
a mano: titolo e date in una finestra, i partecipanti nell'ordine della
classifica finale nell'altra; poi posizioni e medaglie entrano nello storico
dei discepoli come alla finalizzazione, l'archivio si salva e Giocatori.txt
si rigenera.
"""

import copy
from dataclasses import dataclass

import wx

from data import format_date_extended, tournament_registered
from dialogs import ManualUnionDialog, ManualUnionPlayersDialog
from standings import MEDAL_NAMES
from ui_utils import save_or_warn


@dataclass
class EsitoUnione:
    """I conti dell'inserimento: quanti discepoli hanno preso la voce nuova,
    quanti non erano in archivio e quanti avevano gia' questo torneo."""

    aggiornati: int = 0
    nuovi: int = 0
    gia_registrati: int = 0


def registra_classifica(db, titolo, inizio, fine, classifica):
    """Scrive nello storico dei discepoli il torneo con la classifica data:
    il primo dell'elenco e' primo, e cosi' via. Le date arrivano come
    timestamp e vanno nello storico in forma estesa, come alla
    finalizzazione. Chi aveva gia' questo torneo, stesso titolo e stessa
    data d'inizio, resta com'e'. Non salva: lo fa chi chiama.
    """
    esito = EsitoUnione()
    s_fmt, e_fmt = format_date_extended(inizio), format_date_extended(fine)
    for posizione, nome in enumerate(classifica, start=1):
        if nome not in db.players:
            esito.nuovi += 1
        if db.add_or_update_player(nome, posizione, titolo, s_fmt, e_fmt):
            esito.aggiornati += 1
        else:
            esito.gia_registrati += 1
    return esito


def unione_manuale(parent, db):
    """Conduce l'unione manuale dalle due finestre al salvataggio. Da Torna
    a titolo e date si rientra nella prima finestra con i valori scritti, e
    i partecipanti raccolti si ritrovano al passo seguente; Annulla nella
    prima finestra chiude tutto. Restituisce True se il torneo e' stato
    inserito e l'archivio salvato.
    """
    titolo, inizio, fine, partecipanti = "", "", "", []
    while True:
        dlg = ManualUnionDialog(parent, titolo, inizio, fine)
        esito = dlg.ShowModal()
        valori = dlg.valori
        dlg.Destroy()
        if esito != wx.ID_OK or valori is None:
            return False
        titolo, inizio, fine = valori
        dlg2 = ManualUnionPlayersDialog(parent, titolo, partecipanti, db=db)
        esito = dlg2.ShowModal()
        partecipanti = list(dlg2.players)
        dlg2.Destroy()
        if esito != wx.ID_OK:
            continue
        if tournament_registered(db.players, titolo, inizio) and not _conferma_aggiunta(
            titolo, inizio
        ):
            continue
        # Se l'archivio non si salva, in memoria torna com'era: altrimenti un
        # salvataggio riuscito piu' tardi scriverebbe un torneo mai annunciato.
        prima = copy.deepcopy(db.players)
        conti = registra_classifica(db, titolo, inizio, fine, partecipanti)
        if not save_or_warn(db.save, parent):
            db.players = prima
            wx.MessageBox(
                "Il torneo non è stato inserito: l'archivio dei discepoli non "
                "è stato salvato. Risolvi il problema e ripeti l'unione manuale.",
                "Unione manuale non riuscita",
                wx.OK | wx.ICON_ERROR,
            )
            return False
        _annuncia(titolo, inizio, fine, partecipanti, conti)
        return True


def _conferma_aggiunta(titolo, inizio):
    """Il torneo e' gia' nello storico di qualcuno: si aggiungono solo i
    partecipanti che ancora non lo hanno, se l'utente vuole."""
    risposta = wx.MessageBox(
        f"Il torneo {titolo}, iniziato {format_date_extended(inizio)}, è già "
        "nello storico di qualche discepolo. Aggiungo soltanto i partecipanti "
        "che ancora non lo hanno?",
        "Torneo già in archivio",
        wx.YES_NO | wx.ICON_QUESTION,
    )
    return risposta == wx.YES


def _annuncia(titolo, inizio, fine, classifica, conti):
    podio = ", ".join(
        f"{MEDAL_NAMES[pos]} a {nome}"
        for pos, nome in enumerate(classifica, start=1)
        if pos in MEDAL_NAMES
    )
    msg = (
        f"Oh mio archivista supremo! Il torneo {titolo}, da "
        f"{format_date_extended(inizio)} a {format_date_extended(fine)}, è inciso "
        f"nella Hall of Fame con {len(classifica)} partecipanti.\n"
        f"{podio[:1].upper()}{podio[1:]}.\n"
        f"Discepoli aggiornati: {conti.aggiornati}.\n"
    )
    if conti.nuovi:
        msg += f"Nuovi in archivio: {conti.nuovi}.\n"
    if conti.gia_registrati:
        msg += f"Avevano già questo torneo: {conti.gia_registrati}.\n"
    msg += "Il file Giocatori.txt è aggiornato."
    wx.MessageBox(msg, "Unione manuale conclusa", wx.OK | wx.ICON_INFORMATION)
