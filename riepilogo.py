"""Il Riepilogo: la schermata di Dadillo quando non c'e' niente da fare, e su
richiesta con Visualizza, Riepilogo e statistiche (Ctrl+R). Nome e versione,
data e ora, lo stato del torneo con le cose che si possono fare adesso, e le
statistiche dell'archivio dei discepoli (richiesta di Gabriele del 18
novembre 2026, novita' della 2.18.0).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Fino alla 2.17.1 senza un torneo Dadillo apriva subito Nuovo Torneo, e chi
voleva solo guardare l'archivio si trovava a creare un torneo; a torneo
finalizzato mostrava la classifica finale a ogni avvio, e dopo un Nuovo
Torneo annullato restava una riga sola, "L'Altare e' vuoto". Il testo e' in
sola lettura e si legge con le frecce da capo; i pulsanti sotto portano alla
cosa da fare: Nuovo Torneo, Scegli i discepoli, Torna alle Partite, Finalizza
il torneo, Classifica finale.
"""

import datetime
import re

import wx

from data import (
    ITALIAN_MONTHS,
    MEDIA_NON_DISPONIBILE,
    format_date_extended,
    hall_of_fame_ranking,
    now_local,
    placement_stats,
    split_history_entry,
    tournament_sizes,
)
from standings import MEDAL_NAMES
from version import VERSION

PLURALI = {"oro": "ori", "argento": "argenti", "bronzo": "bronzi", "legno": "legni"}
QUANTI_IN_VETTA = 5

# Gli stati del torneo caricato. Per ognuno i pulsanti sotto il testo:
# etichetta e metodo della finestra principale che il pulsante chiama.
VUOTO = "vuoto"
PREPARAZIONE = "preparazione"
IN_CORSO = "in_corso"
CONCLUSO = "concluso"
FINALIZZATO = "finalizzato"
PULSANTI = {
    VUOTO: [("&Nuovo Torneo", "on_menu_new")],
    PREPARAZIONE: [("&Scegli i discepoli", "resume_setup_players"), ("&Nuovo Torneo", "on_menu_new")],
    IN_CORSO: [("&Torna alle Partite", "init_main_ui")],
    CONCLUSO: [("&Finalizza il torneo", "avvia_finalizzazione"), ("&Torna alle Partite", "init_main_ui")],
    FINALIZZATO: [("&Classifica finale", "show_standings"), ("&Nuovo Torneo", "on_menu_new")],
}
AZIONI_COMUNI = [
    "- Classifica Generale (Hall of Fame), nel menu Giocatori: tutto l'archivio, "
    "ordinabile per punti, medaglie, media piazzamenti e tornei.",
    "- Gestione Giocatori DB, nel menu Giocatori: lo storico di ogni discepolo, "
    "da rinominare o correggere.",
    "- Unione manuale, nel menu Opzioni: un torneo giocato altrove entra nella "
    "Hall of Fame; Unisci Database Giocatori fonde l'archivio di un altro Dadillo.",
    "- Chiedi aiuto al PUB, nel menu Aiuto, se qualcosa non torna.",
]


def stato_del_torneo(tourney):
    """In che stato e' il torneo caricato: senza titolo e' vuoto; con il
    titolo ma senza partite e' in preparazione; poi in corso, concluso senza
    finalizzazione, finalizzato."""
    if not tourney.title:
        return VUOTO
    if not tourney.unplayed_matches and not tourney.played_matches:
        return PREPARAZIONE
    if not tourney.concluso():
        return IN_CORSO
    return FINALIZZATO if tourney.finalized else CONCLUSO


def data_da_estesa(testo):
    """La data da una forma estesa dello storico, "martedì 17 marzo 2026":
    None se non si riconosce."""
    trovata = re.search(r"(\d{1,2})\s+([^\W\d_]+)\s+(\d{4})", str(testo).lower())
    if not trovata or trovata.group(2) not in ITALIAN_MONTHS:
        return None
    try:
        return datetime.date(
            int(trovata.group(3)),
            ITALIAN_MONTHS.index(trovata.group(2)) + 1,
            int(trovata.group(1)),
        )
    except ValueError:
        return None


def tornei_dell_archivio(players):
    """I tornei registrati nello storico, dal piu' vecchio: per ognuno titolo,
    date, partecipanti e i discepoli per posizione. Quelli con una data che
    non si legge vanno in fondo."""
    tornei = {}
    for nome, dati in players.items():
        for voce in dati.get("history", []) or []:
            pos, titolo, inizio, fine = split_history_entry(voce)
            if pos is None:
                continue
            torneo = tornei.setdefault(
                (titolo, inizio),
                {"titolo": titolo, "inizio": inizio, "fine": fine, "piazzamenti": {}},
            )
            torneo["piazzamenti"].setdefault(pos, []).append(nome)
    misure = tournament_sizes(players)
    for chiave, torneo in tornei.items():
        torneo["partecipanti"] = misure.get(chiave, len(torneo["piazzamenti"]))
        torneo["data"] = data_da_estesa(torneo["inizio"])
    return sorted(
        tornei.values(),
        key=lambda t: (t["data"] is None, t["data"] or datetime.date.min, t["titolo"]),
    )


def medaglie_in_parole(medaglie):
    """Il medagliere in parole: "2 ori, 1 argento", oppure nessuna medaglia."""
    parti = []
    for medaglia in ("oro", "argento", "bronzo", "legno"):
        quante = medaglie.get(medaglia, 0)
        if quante:
            parti.append(f"{quante} {medaglia if quante == 1 else PLURALI[medaglia]}")
    return ", ".join(parti) if parti else "nessuna medaglia"


def _elenco(nomi):
    """Nomi in fila, con la e prima dell'ultimo."""
    nomi = list(nomi)
    if len(nomi) <= 1:
        return "".join(nomi)
    return ", ".join(nomi[:-1]) + " e " + nomi[-1]


def _podio(torneo):
    return ", ".join(
        f"{MEDAL_NAMES[pos]} a {_elenco(torneo['piazzamenti'][pos])}"
        for pos in sorted(MEDAL_NAMES)
        if pos in torneo["piazzamenti"]
    )


def _partite_giocate(quante):
    return "1 partita giocata" if quante == 1 else f"{quante} partite giocate"


def _tornei(quanti):
    return "1 torneo" if quanti == 1 else f"{quanti} tornei"


def _periodo(inizio, fine):
    """Le date di un torneo in parole: da e a, oppure una sola se un torneo
    e' cominciato e finito lo stesso giorno."""
    if inizio == fine:
        return f"giocato {inizio}"
    return f"da {inizio} a {fine}"


def _discepoli(quanti):
    return "1 discepolo" if quanti == 1 else f"{quanti} discepoli"


def _tutte_giocate(quante):
    if quante == 1:
        return "l'unica partita è giocata"
    return f"tutte le {quante} partite sono giocate"


def righe_stato(tourney, stato):
    """Lo stato del torneo in una frase, e le cose da fare adesso."""
    inizio = format_date_extended(tourney.start_date) or "data sconosciuta"
    fine = format_date_extended(tourney.end_date) or "data sconosciuta"
    giocate, da_giocare = len(tourney.played_matches), len(tourney.unplayed_matches)
    if stato == VUOTO:
        righe = [
            "L'altare è libero: nessun torneo in corso.",
            "Cosa puoi fare adesso:",
            "- Nuovo Torneo, nel menu File o Ctrl+N, oppure il pulsante qui sotto: "
            "nome e regole, poi i discepoli, e le sfide nascono da sole.",
        ]
    elif stato == PREPARAZIONE:
        righe = [
            f"Il torneo {tourney.title} è in preparazione: mancano i discepoli.",
            "Cosa puoi fare adesso:",
            "- Scegli i discepoli, col pulsante qui sotto, per completare il torneo.",
            "- Nuovo Torneo, nel menu File o Ctrl+N, per ricominciare da capo.",
        ]
    elif stato == IN_CORSO:
        righe = [
            f"Torneo in corso: {tourney.title}, {_discepoli(len(tourney.players))}, "
            f"{_partite_giocate(giocate)} e {da_giocare} da giocare, iniziato {inizio}.",
            "Cosa puoi fare adesso:",
            "- Torna alle Partite, col pulsante qui sotto, per inserire i risultati.",
            "- Classifica, nel menu Visualizza o Ctrl+L: la classifica parziale.",
        ]
    elif stato == CONCLUSO:
        righe = [
            f"Il torneo {tourney.title} è concluso: {_tutte_giocate(giocate)}, ma "
            "medaglie e piazzamenti non sono ancora nella Hall of Fame.",
            "Cosa puoi fare adesso:",
            "- Finalizza il torneo, col pulsante qui sotto o con Classifica nel menu "
            "Visualizza, Ctrl+L.",
            "- Torna alle Partite, per correggere un risultato prima della finalizzazione.",
        ]
    else:
        righe = [
            f"L'ultimo torneo, {tourney.title}, {_periodo(inizio, fine)}, è concluso e "
            "finalizzato: medaglie e piazzamenti sono nella Hall of Fame.",
            "Cosa puoi fare adesso:",
            "- Classifica finale, col pulsante qui sotto o con Ctrl+L.",
            "- Nuovo Torneo, nel menu File o Ctrl+N: il torneo concluso lascia il "
            "posto a quello nuovo.",
        ]
    return righe + AZIONI_COMUNI


def _righe_tornei(tornei):
    righe = []
    quanti = len(tornei)
    affollato = max(tornei, key=lambda t: t["partecipanti"])
    if quanti == 1:
        righe.append(
            f"L'unico torneo, {affollato['titolo']}, ha avuto "
            f"{affollato['partecipanti']} partecipanti."
        )
    else:
        intimo = min(tornei, key=lambda t: t["partecipanti"])
        media = sum(t["partecipanti"] for t in tornei) / quanti
        righe.append(
            f"Il più affollato: {affollato['titolo']} con {affollato['partecipanti']} "
            f"partecipanti; il più intimo: {intimo['titolo']} con "
            f"{intimo['partecipanti']}; in media {media:.1f} per torneo."
        )
        primo = tornei[0]
        righe.append(f"Il primo torneo: {primo['titolo']}, iniziato {primo['inizio']}.")
    ultimo = tornei[-1]
    righe.append(
        f"L'ultimo torneo: {ultimo['titolo']}, {_periodo(ultimo['inizio'], ultimo['fine'])}: "
        f"{_podio(ultimo)}."
    )
    durate = []
    for torneo in tornei:
        fine = data_da_estesa(torneo["fine"])
        if torneo["data"] and fine and fine >= torneo["data"]:
            durate.append((torneo, (fine - torneo["data"]).days + 1))
    if len(durate) > 1:
        lungo, giorni = max(durate, key=lambda coppia: coppia[1])
        righe.append(f"Il torneo più lungo: {lungo['titolo']}, {giorni} giorni.")
    return righe


def _righe_vetta(players):
    classifica = list(hall_of_fame_ranking(players))
    righe = [f"I primi {min(QUANTI_IN_VETTA, len(classifica))} della Hall of Fame, per punti:"]
    for ordinale, nome, punti in classifica[:QUANTI_IN_VETTA]:
        num_tornei, _, media = placement_stats(players[nome])
        righe.append(
            f"{ordinale}° {nome}: {punti:.1f} punti, "
            f"{medaglie_in_parole(players[nome].get('medals', {}))}, "
            f"{_tornei(num_tornei)}, media {media}."
        )
    punti_di = {nome: punti for _, nome, punti in classifica}
    medagliati = [
        nome for nome in players if any((players[nome].get("medals") or {}).values())
    ]
    medagliati.sort(
        key=lambda nome: (
            tuple(players[nome]["medals"].get(m, 0) for m in ("oro", "argento", "bronzo", "legno")),
            punti_di.get(nome, 0),
        ),
        reverse=True,
    )
    if medagliati:
        righe.append(
            f"I primi {min(QUANTI_IN_VETTA, len(medagliati))} del medagliere, "
            "ori, poi argenti, bronzi e legni:"
        )
        for posto, nome in enumerate(medagliati[:QUANTI_IN_VETTA], 1):
            righe.append(f"{posto}. {nome}: {medaglie_in_parole(players[nome]['medals'])}.")
    return righe


def _righe_curiosita(players, tornei):
    righe = ["Curiosità:"]
    quanti_tornei = len(tornei)
    presenze = {nome: placement_stats(dati)[0] for nome, dati in players.items()}
    massimo = max(presenze.values())
    assidui = sorted(nome for nome, n in presenze.items() if n == massimo)
    if massimo == quanti_tornei and quanti_tornei > 1:
        righe.append(f"Hanno giocato tutti i {quanti_tornei} tornei: {_elenco(assidui)}.")
    elif quanti_tornei > 1:
        righe.append(
            f"I più assidui: {_elenco(assidui)}, con {_tornei(massimo)} su {quanti_tornei}."
        )
    debuttanti = sum(1 for n in presenze.values() if n == 1)
    if debuttanti and quanti_tornei > 1:
        righe.append(f"Discepoli con un torneo solo: {debuttanti}.")
    ori = {nome: (dati.get("medals") or {}).get("oro", 0) for nome, dati in players.items()}
    vincitori = sorted(nome for nome, n in ori.items() if n)
    if vincitori:
        piu_ori = max(ori.values())
        if piu_ori > 1:
            campioni = sorted(nome for nome, n in ori.items() if n == piu_ori)
            righe.append(
                f"Gli ori sono andati a {len(vincitori)} discepoli diversi; "
                f"il più vincente: {_elenco(campioni)} con {piu_ori} ori."
            )
        else:
            righe.append(
                f"Nessuno ha ancora vinto due volte: {len(vincitori)} vincitori "
                f"diversi in {_tornei(quanti_tornei)}."
            )
    medie = {
        nome: placement_stats(dati)[1]
        for nome, dati in players.items()
        if placement_stats(dati)[0] >= 2 and placement_stats(dati)[1] != MEDIA_NON_DISPONIBILE
    }
    if medie:
        migliore = min(medie.values())
        nomi = sorted(nome for nome, media in medie.items() if media == migliore)
        righe.append(
            f"La media piazzamenti migliore, con almeno due tornei: {_elenco(nomi)}, "
            f"{migliore:.2f}."
        )
    legni = {nome: (dati.get("medals") or {}).get("legno", 0) for nome, dati in players.items()}
    piu_legni = max(legni.values())
    if piu_legni:
        re_del_legno = sorted(nome for nome, n in legni.items() if n == piu_legni)
        titolo = "Il re del legno" if len(re_del_legno) == 1 else "I re del legno"
        righe.append(
            f"{titolo}: {_elenco(re_del_legno)}, con {piu_legni} "
            f"{'quarto posto' if piu_legni == 1 else 'quarti posti'}."
        )
    ultimi = {}
    for torneo in tornei:
        for nome in torneo["piazzamenti"].get(torneo["partecipanti"], []):
            ultimi[nome] = ultimi.get(nome, 0) + 1
    if ultimi and max(ultimi.values()) > 1:
        volte = max(ultimi.values())
        fanalini = sorted(nome for nome, n in ultimi.items() if n == volte)
        righe.append(f"Il fanalino di coda più fedele: {_elenco(fanalini)}, ultimo {volte} volte.")
    return righe


def righe_archivio(players):
    """Le statistiche dell'archivio dei discepoli."""
    righe = ["L'archivio dei discepoli:"]
    tornei = tornei_dell_archivio(players)
    if not players or not tornei:
        righe.append(
            f"{_discepoli(len(players))} e nessun torneo registrato: la Hall of Fame "
            "aspetta la prima finalizzazione."
            if players
            else "Ancora nessun discepolo: la Hall of Fame aspetta il primo torneo."
        )
        return righe
    partecipazioni = sum(
        len(nomi) for torneo in tornei for nomi in torneo["piazzamenti"].values()
    )
    righe.append(
        f"{_discepoli(len(players))}, {_tornei(len(tornei))} e {partecipazioni} "
        "partecipazioni registrate."
    )
    righe += _righe_tornei(tornei)
    righe += _righe_vetta(players)
    righe += _righe_curiosita(players, tornei)
    return righe


def testo_riepilogo(players, tourney, adesso=None):
    """Il testo intero del riepilogo, una riga per informazione."""
    adesso = adesso or now_local()
    righe = [
        f"Dadillo {VERSION}, L'Altare del Sacrificio.",
        f"{format_date_extended(adesso).capitalize()}, ore {adesso:%H:%M}.",
    ]
    righe += righe_stato(tourney, stato_del_torneo(tourney))
    righe += righe_archivio(players)
    return "\n".join(righe)


class RiepilogoPanel(wx.Panel):
    """La schermata del riepilogo: il testo in sola lettura, dove arriva il
    fuoco e che si legge con le frecce da capo, e sotto i pulsanti dello
    stato del torneo, che chiamano i metodi della finestra principale."""

    def __init__(self, parent, tourney, db):
        super().__init__(parent)
        self.stato = stato_del_torneo(tourney)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.txt = wx.TextCtrl(
            self,
            value=testo_riepilogo(db.players, tourney),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
        )
        self.txt.SetName("Riepilogo")
        sizer.Add(self.txt, 1, wx.EXPAND | wx.ALL, 10)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsanti = []
        for etichetta, metodo in PULSANTI[self.stato]:
            bottone = wx.Button(self, label=etichetta)
            bottone.Bind(wx.EVT_BUTTON, lambda event, m=metodo: getattr(self.GetParent(), m)())
            riga.Add(bottone, 0, wx.ALL, 5)
            self.pulsanti.append(bottone)
        sizer.Add(riga, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)
        self.SetSizer(sizer)
        self.txt.SetInsertionPoint(0)
        self.txt.ShowPosition(0)
        wx.CallAfter(self.txt.SetFocus)
