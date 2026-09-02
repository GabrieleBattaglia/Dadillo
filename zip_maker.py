"""Comprime la cartella prodotta da PyInstaller in un solo archivio.

I file estratti devono stare alla radice dell'archivio, senza cartelle
intermedie: e' quello che l'auto updater di GBUtils sa gestire, e gli
strumenti di compressione di Windows non lo fanno.

Quello che non deve entrare nel pacchetto pubblico viene lasciato fuori anche
qui, oltre che ripulito a mano prima di comprimere: torneo, impostazioni,
archivio dei discepoli, Hall of Fame e copie di sicurezza nascono accanto
all'eseguibile appena lo si avvia per la prova, e senza questa rete di
sicurezza finirebbero nell'archivio insieme ai dati di chi ha compilato.

Il filtro sui nomi vale soltanto per i file accanto all'eseguibile: dentro
_internal c'e' quello che ha messo PyInstaller, compreso base_library.zip,
e serve tutto.

Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import os
import sys
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARTELLA = os.path.join(BASE_DIR, "dist", "Dadillo")
ARCHIVIO = os.path.join(BASE_DIR, "Dadillo.zip")
CARTELLE_ESCLUSE = {"__pycache__", ".git", "log", "settings", "materiali"}
# File di lavoro e dati personali che nascono provando l'eseguibile
FILE_ESCLUSI = {
    "dadillo.json",
    "dadillo_settings.json",
    "dadillo_players.json",
    "giocatori.txt",
}
CODE_ESCLUSE = (".bak", ".tmp", ".pdb", ".log", ".pyc", ".zip")


def da_escludere(nome):
    """Vero se il file, che sta accanto all'eseguibile, non va nel pacchetto."""
    minuscolo = nome.lower()
    if minuscolo in FILE_ESCLUSI:
        return True
    if minuscolo.endswith(CODE_ESCLUSE):
        return True
    # Copie dei file danneggiati messe da parte da Dadillo
    return ".danneggiato_" in minuscolo


def main():
    print(f"Creo {ARCHIVIO} a partire da {CARTELLA}.")
    if not os.path.isdir(CARTELLA):
        print(f"La cartella {CARTELLA} non esiste: PyInstaller ha finito?")
        return 1
    quanti = 0
    lasciati = []
    with zipfile.ZipFile(ARCHIVIO, "w", zipfile.ZIP_DEFLATED) as archivio:
        for radice, cartelle, file in os.walk(CARTELLA):
            cartelle[:] = [c for c in cartelle if c not in CARTELLE_ESCLUSE]
            alla_radice = os.path.abspath(radice) == os.path.abspath(CARTELLA)
            for nome in file:
                if alla_radice and da_escludere(nome):
                    lasciati.append(nome)
                    continue
                percorso = os.path.join(radice, nome)
                archivio.write(percorso, os.path.relpath(percorso, CARTELLA))
                quanti += 1
    print(f"Fatto: {ARCHIVIO} contiene {quanti} file.")
    if lasciati:
        print(f"Lasciati fuori {len(lasciati)} file di lavoro: {lasciati}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
