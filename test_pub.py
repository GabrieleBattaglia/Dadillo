"""Le parole delle due voci del PUB, dalla 2.15.0 (issue 15).
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Fable 5.1, modalita' auto.

Qui si guardano soltanto le parole: il programma di posta e gli appunti non
si toccano mai, perche' nessuna prova apre la finestra ne' chiama apri_mail.
Le informazioni sul computer, dove servono vere, si leggono soltanto.
"""

import sys

import pytest

import pub

INFORMAZIONI = [
    ("windows", "Windows 11 Pro"),
    ("windows_versione", "25H2"),
    ("nuclei", 32),
    ("screen_reader", "NVDA 2026.3"),
    ("scala", None),
    ("python", "3.14.5 64 bit"),
    ("compilato", True),
]


def test_la_mail_d_iscrizione():
    from GBUtils import PUB_ISCRIZIONE

    mail = pub.mail_d_iscrizione()
    assert mail["destinatario"] == PUB_ISCRIZIONE == "prg-user-blind+subscribe@googlegroups.com"
    assert "così com'è" in mail["corpo"] and "confermare" in mail["corpo"]
    assert "{programma}" in mail["spiegazione"] and "Dadillo non spedisce" in mail["spiegazione"]
    assert len(mail["passi"]) == 2
    assert mail["passi"][0][1] == PUB_ISCRIZIONE
    assert mail["passi"][1][1] is None


def test_la_mail_d_aiuto_dal_pacchetto_compilato():
    from GBUtils import PUB_GRUPPO

    mail = pub.mail_d_aiuto("2.15.0", True, INFORMAZIONI)
    assert mail["destinatario"] == PUB_GRUPPO == "prg-user-blind@googlegroups.com"
    assert mail["oggetto"] == "Chiedo per Dadillo 2.15.0"
    righe = mail["corpo"].split("\n")
    assert righe[0] == "Scrivi qui la tua domanda, al posto di questa riga."
    assert righe[2] == "Programma: Dadillo 2.15.0, pacchetto compilato"
    assert righe[3:] == [
        "Sistema operativo: Windows 11 Pro",
        "Versione di Windows: 25H2",
        "Nuclei logici: 32",
        "Screen reader: NVDA 2026.3",
        "Python: 3.14.5 64 bit",
    ]
    # La chiave compilato non ha etichetta, e un valore None resta fuori.
    assert "compilato" not in mail["corpo"].lower().replace("pacchetto compilato", "")
    assert "Scala" not in mail["corpo"]
    assert "Chiedo per Dadillo 2.15.0" in mail["spiegazione"]
    assert "{programma}" in mail["spiegazione"]


def test_i_passi_della_mail_d_aiuto():
    from GBUtils import PUB_GRUPPO

    mail = pub.mail_d_aiuto("2.15.0", False, INFORMAZIONI)
    assert "Programma: Dadillo 2.15.0, dai sorgenti" in mail["corpo"]
    passi = mail["passi"]
    assert [istruzione.split(".")[0] for istruzione, _ in passi] == [f"Passo {i} di 4" for i in range(1, 5)]
    assert [testo for _, testo in passi] == [PUB_GRUPPO, mail["oggetto"], mail["corpo"], None]
    assert "Entra al PUB, nel menu Aiuto" in passi[-1][0]


def test_i_pulsanti_e_le_parole_fisse():
    assert set(pub.PULSANTI) == {"apri", "passi", "ok", "chiudi", "annulla"}
    assert all(etichetta.startswith("&") for etichetta in pub.PULSANTI.values())
    assert pub.PAROLE == {True: "sì", False: "no"}
    assert "webmail" in pub.SENZA_POSTA


@pytest.mark.skipif(sys.platform != "win32", reason="le informazioni di sistema si leggono in Windows")
def test_le_etichette_corrispondono_alle_chiavi_di_gbutils():
    from GBUtils import informazioni_di_sistema

    chiavi = {chiave for chiave, _ in informazioni_di_sistema()}
    assert set(pub.ETICHETTE) <= chiavi
    assert "compilato" in chiavi and "compilato" not in pub.ETICHETTE


@pytest.mark.finestre_vere
@pytest.mark.skipif(sys.platform != "win32", reason="il desktop nascosto esiste solo in Windows")
def test_la_finestra_di_gbwx_accetta_le_parole_di_dadillo():
    """La finestra che prepara la mail si apre davvero, sul desktop nascosto,
    con le parole di Dadillo, e si chiude da sola senza aprire niente: e'
    la prova che le due voci del menu arrivano a una finestra intera."""
    import wx
    from GBwx import finestra_mail

    app = wx.App(False)
    chiuse = []

    def chiudi():
        for finestra in wx.GetTopLevelWindows():
            if isinstance(finestra, wx.Dialog) and finestra.IsModal():
                chiuse.append(finestra.GetTitle())
                finestra.EndModal(wx.ID_CANCEL)

    for mail in (pub.mail_d_iscrizione(), pub.mail_d_aiuto("2.15.0", False, INFORMAZIONI)):
        wx.CallLater(400, chiudi)
        riuscita = finestra_mail(
            None, mail["titolo"], mail["destinatario"], mail["oggetto"], mail["corpo"],
            mail["spiegazione"], mail["passi"], pub.PULSANTI, pub.SENZA_POSTA,
        )
        assert riuscita is False
    app.Destroy()
    assert chiuse == ["Entra al PUB, il gruppo di supporto", "Chiedi aiuto al PUB"]


@pytest.mark.skipif(sys.platform != "win32", reason="le informazioni di sistema si leggono in Windows")
def test_il_mailto_con_le_informazioni_vere_resta_corto():
    """Certi programmi di posta tagliano gli indirizzi oltre i duemila
    caratteri circa: la mail d'aiuto, con le informazioni di questa
    macchina, deve restare sotto con un buon margine."""
    from GBUtils import indirizzo_mailto, informazioni_di_sistema

    mail = pub.mail_d_aiuto("2.15.0", True, informazioni_di_sistema())
    indirizzo = indirizzo_mailto(mail["destinatario"], mail["oggetto"], mail["corpo"])
    assert len(indirizzo) < 1500, len(indirizzo)
