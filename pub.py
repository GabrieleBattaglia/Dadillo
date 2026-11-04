"""Dadillo, le parole delle due voci del PUB, il gruppo di supporto: la mail
che iscrive e quella che chiede aiuto (issue 15, richiesta di Gabriele del 21
ottobre 2026 per tutti i programmi del parco che hanno una finestra).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Gli indirizzi, le informazioni sul computer e la composizione della mail
vengono da GBUtils, la finestra che la prepara da GBwx, finestra_mail: qui ci
sono soltanto le parole di Dadillo, perche' GBUtils non ne ha di sue. La
finestra si apre sempre, anche quando il programma di posta c'e', perche' il
nuovo Outlook di Windows 11 e' spesso associato a mailto anche per chi non lo
usa; senza posta accompagna l'utente un passo alla volta, copiando negli
appunti un campo per volta. Dadillo non spedisce mai niente: spedisce
l'utente, se vuole, dopo aver letto e corretto. Modello: pub.py di MeTeOra
2.1.0, senza i registri degli errori, che Dadillo non tiene.
"""

PULSANTI = {
    "apri": "&Apri nel programma di posta",
    "passi": "&Passo per passo",
    "ok": "&OK",
    "chiudi": "&Chiudi",
    "annulla": "&Annulla",
}
SENZA_POSTA = (
    "Non trovo un programma di posta, oppure non si è aperto: prepariamo la mail "
    "un pezzo alla volta, da incollare nella tua posta, per esempio nella webmail "
    "del browser."
)
# Le informazioni del computer nella mail d'aiuto, nell'ordine in cui
# compaiono; quelle che non si leggono restano fuori. Se il programma e'
# compilato lo dice gia' la riga del programma, quindi la chiave compilato
# non ha etichetta.
ETICHETTE = {
    "windows": "Sistema operativo",
    "windows_versione": "Versione di Windows",
    "windows_build": "Build di Windows",
    "architettura": "Architettura",
    "processore": "Processore",
    "nuclei": "Nuclei logici",
    "memoria_totale": "Memoria",
    "memoria_libera": "Memoria libera",
    "lingua": "Lingua di sistema",
    "screen_reader": "Screen reader",
    "schermo": "Schermo",
    "scala": "Scala dello schermo",
    "python": "Python",
}
PAROLE = {True: "sì", False: "no"}
_ALTRA_STRADA = (
    "Se la mail non compare, torna qui e scegli Passo per passo: ti guido a "
    "scriverla nella tua posta, per esempio nella webmail del browser."
)
_ISCRIVITI = "Se non sei ancora iscritto al PUB, puoi farlo con Entra al PUB, nel menu Aiuto."


def mail_d_iscrizione():
    """Entra al PUB: le parole della mail che iscrive al gruppo. All'indirizzo
    dell'iscrizione Google non legge oggetto e testo, e risponde con una mail
    di conferma: nei passi basta l'indirizzo."""
    from GBUtils import PUB_ISCRIZIONE

    return {
        "titolo": "Entra al PUB, il gruppo di supporto",
        "destinatario": PUB_ISCRIZIONE,
        "oggetto": "Iscrizione al PUB",
        "corpo": (
            "Invia questo messaggio così com'è per iscriverti al PUB. Google ti "
            "scriverà per chiederti di confermare."
        ),
        "spiegazione": "\n".join((
            "Il PUB è il gruppo di supporto dei programmi di Gabriele Battaglia, una "
            "lista di posta su Google Groups, dove si chiede aiuto, si segnalano i "
            "problemi e si propongono idee.",
            "Il pulsante Apri nel programma di posta prepara in {programma} la mail "
            "che ti iscrive: spediscila così com'è, perché Dadillo non spedisce "
            "niente da solo. Poi Google ti scriverà per chiederti di confermare "
            "l'iscrizione: segui le sue istruzioni.",
            _ALTRA_STRADA,
        )),
        "passi": (
            (
                "Passo 1 di 2. Scrivi una mail nuova nella tua posta, per esempio nella "
                "webmail del browser, e incolla nel campo A l'indirizzo dell'iscrizione, "
                "che ho copiato negli appunti; poi torna qui e premi OK. L'indirizzo è "
                "questo:",
                PUB_ISCRIZIONE,
            ),
            (
                "Passo 2 di 2. Oggetto e testo possono restare vuoti, perché Google non "
                "li legge: spedisci la mail così com'è. Google ti scriverà per chiederti "
                "di confermare l'iscrizione: segui le sue istruzioni. OK chiude questa "
                "finestra.",
                None,
            ),
        ),
    }


def mail_d_aiuto(versione, compilato, informazioni=None):
    """Chiedi aiuto al PUB: le parole della mail al gruppo. L'oggetto dice la
    versione; il testo ha una prima riga da sostituire con la domanda e sotto
    le informazioni: il programma, con la versione e se gira compilato o dai
    sorgenti, e il computer, da informazioni_di_sistema di GBUtils con le
    etichette italiane. informazioni sono le coppie di chiave e valore; se
    mancano le legge righe_informazioni."""
    from GBUtils import PUB_GRUPPO, righe_informazioni

    oggetto = f"Chiedo per Dadillo {versione}"
    corpo = "\n".join((
        "Scrivi qui la tua domanda, al posto di questa riga.",
        "Informazioni utili per chi ti risponde, che puoi cancellare se preferisci:",
        f"Programma: Dadillo {versione}, {'pacchetto compilato' if compilato else 'dai sorgenti'}",
        *righe_informazioni(ETICHETTE, informazioni, PAROLE),
    ))
    passi = (
        (
            "Passo 1 di 4. Scrivi una mail nuova nella tua posta, per esempio nella "
            "webmail del browser, e incolla nel campo A l'indirizzo del PUB, che ho "
            "copiato negli appunti; poi torna qui e premi OK. L'indirizzo è questo:",
            PUB_GRUPPO,
        ),
        (
            "Passo 2 di 4. Incolla nel campo Oggetto quello che ho copiato negli "
            "appunti, poi torna qui e premi OK. L'oggetto è questo:",
            oggetto,
        ),
        (
            "Passo 3 di 4. Incolla nel testo della mail quello che ho copiato negli "
            "appunti, e scrivi la tua domanda al posto della prima riga; le "
            "informazioni su Dadillo e sul computer, sotto, puoi cancellarle se "
            "preferisci. Poi torna qui e premi OK. Il testo è questo:",
            corpo,
        ),
        (f"Passo 4 di 4. Spedisci la mail. {_ISCRIVITI} OK chiude questa finestra.", None),
    )
    return {
        "titolo": "Chiedi aiuto al PUB",
        "destinatario": PUB_GRUPPO,
        "oggetto": oggetto,
        "corpo": corpo,
        "spiegazione": "\n".join((
            "Il pulsante Apri nel programma di posta prepara in {programma} una mail "
            "al PUB, il gruppo di supporto dei programmi di Gabriele Battaglia, con "
            f"l'oggetto {oggetto}.",
            "Scrivi la tua domanda al posto della prima riga del testo; sotto ci sono "
            "le informazioni su Dadillo e sul tuo computer, utili a chi ti risponde, "
            "che puoi cancellare se preferisci.",
            f"Poi spediscila tu: Dadillo non spedisce niente da solo. {_ISCRIVITI}",
            _ALTRA_STRADA,
        )),
        "passi": passi,
    }
