"""La finalizzazione del torneo: i criteri ufficiali confermati, medaglie e
piazzamenti incisi nella Hall of Fame, e solo dopo la classifica finale
(issue 16, richiesta di Gabriele del 4 novembre 2026).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Fino alla 2.15.0 la premiazione stava nella schermata della classifica
finale, dietro il pulsante Avanti: chi inseriva l'ultimo risultato leggeva la
classifica e spesso non lo premeva, e l'archivio dei discepoli restava
indietro. Dalla 2.16.0 la finestra di finalizzazione viene prima della
classifica, e il torneo si segna come finalizzato nel suo file: finche' non
lo e', la classifica finale non si apre e la finalizzazione viene riproposta
a ogni avvio e dalla voce Classifica.
Le funzioni erano metodi di StandingsPanel in standings.py, da cui arrivano
con lo stesso comportamento: la conferma delle parita' in zona medaglie, la
revisione uno per uno o tutti in massa, l'archivio salvato e l'annuncio.
"""

import wx

from data import format_date_extended
from dialogs import FinalizeTournamentDialog, SinglePlayerReviewDialog
from standings import (
    MEDAL_NAMES,
    classifica_ufficiale,
    draw_split_del_torneo,
    salva_criteri,
)
from ui_utils import save_or_warn


def finalizza_torneo(parent, tourney, settings, player_db):
    """Conduce la finalizzazione del torneo concluso, dalla finestra dei
    criteri all'annuncio.
    Restituisce True se il torneo e' finalizzato, cioe' medaglie e
    piazzamenti sono stati registrati, o saltati di proposito uno per uno, e
    il segno e' stato scritto nel file del torneo. False se l'utente ha
    rimandato, se non ha confermato una parita' in zona medaglie o se
    l'archivio dei discepoli non si e' potuto salvare: allora niente e'
    cambiato, e la finalizzazione tornera'.
    """
    dlg = FinalizeTournamentDialog(parent, tourney, settings)
    esito = dlg.ShowModal()
    scelta, criteri = dlg.choice, dlg.criteri()
    dlg.Destroy()
    if esito != wx.ID_OK or scelta is None:
        return False
    salva_criteri(tourney, criteri, parent)
    # La classifica ufficiale ha sempre il migliore in cima, qualunque vista
    # fosse scelta nella schermata della classifica.
    ufficiale = classifica_ufficiale(tourney, criteri, draw_split_del_torneo(tourney, settings))
    if not _conferma_parita_in_medaglia(ufficiale):
        return False
    registrati = _registra_medaglie(parent, tourney, player_db, ufficiale, scelta)
    if registrati is None:
        return False
    tourney.finalized = True
    save_or_warn(tourney.save, parent)
    _annuncia_premiazione(*registrati)
    return True


def _conferma_parita_in_medaglia(official_standings):
    """Se una medaglia sta per essere assegnata solo per ordine alfabetico
    l'utente deve saperlo prima, non scoprirlo a premiazione avvenuta.
    Restituisce True se si puo' procedere.
    """
    parita_in_medaglia = [
        row for row in official_standings[: len(MEDAL_NAMES)] if row.get("tied_with")
    ]
    if not parita_in_medaglia:
        return True
    elenco = "; ".join(
        f"{row['name']} con {', '.join(row['tied_with'])}" for row in parita_in_medaglia
    )
    risposta = wx.MessageBox(
        "Attenzione, ci sono parita' che nessuno spareggio ha sciolto e che "
        "toccano le prime quattro posizioni: "
        f"{elenco}.\n"
        "Le medaglie verrebbero assegnate in ordine alfabetico. Procedo?",
        "Parita' non risolta",
        wx.YES_NO | wx.ICON_WARNING,
    )
    return risposta == wx.YES


def _registra_medaglie(parent, tourney, db, official_standings, choice):
    """Scrive posizioni e medaglie nello storico dei discepoli.
    Con choice uguale a individual ogni discepolo passa dalla sua finestra di
    revisione, e si puo' saltare; con mass si registrano tutti.
    Restituisce aggiornati e saltati, oppure None se l'archivio non si e'
    potuto salvare, e allora la premiazione non e' registrata.
    """
    updates_done = 0
    skipped_count = 0

    start = format_date_extended(tourney.start_date) if tourney.start_date else "Sconosciuta"
    end = format_date_extended(tourney.end_date) if tourney.end_date else "Sconosciuta"

    for idx, row in enumerate(official_standings):
        name = row["name"]
        pos = idx + 1
        med_str = MEDAL_NAMES.get(pos, "")

        do_update = True
        if choice == "individual":
            rev_dlg = SinglePlayerReviewDialog(
                parent,
                player_name=name,
                position=pos,
                medal_str=med_str,
                tourney_title=tourney.title,
                start_date=start,
                end_date=end,
                tied_with=row.get("tied_with"),
            )
            res = rev_dlg.ShowModal()
            rev_dlg.Destroy()
            if res != wx.ID_OK:
                do_update = False
                skipped_count += 1

        if do_update:
            if db.add_or_update_player(name, pos, tourney.title, start, end):
                updates_done += 1
            else:
                skipped_count += 1

    if not save_or_warn(db.save, parent):
        wx.MessageBox(
            "Le medaglie non sono state registrate: l'archivio dei discepoli "
            "non e' stato salvato. Risolvi il problema e ripeti la "
            "finalizzazione, che ti verra' riproposta.",
            "Premiazione non registrata",
            wx.OK | wx.ICON_ERROR,
        )
        return None
    return updates_done, skipped_count


def _annuncia_premiazione(updates_done, skipped_count):
    msg = (
        "Oh mio insuperabile dominatore! I verdetti sono stati incisi nella "
        "Hall of Fame.\n"
        f"Discepoli aggiornati: {updates_done}.\n"
    )
    if skipped_count > 0:
        msg += f"Saltati o già registrati: {skipped_count}.\n"

    msg += "Il file Giocatori.txt è aggiornato.\nGloria eterna!"

    wx.MessageBox(msg, "Premiazione e Registrazione Conclusa", wx.OK | wx.ICON_INFORMATION)
