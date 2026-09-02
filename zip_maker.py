# Dadillo, utilita': prepara l'archivio per la distribuzione.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5, modalita' auto).
# 02/09/2026: il lavoro e' passato a crea_archivio_release di GBUtils V93.

"""Comprime la cartella prodotta da PyInstaller in un solo archivio.

Tutto il mestiere sta in GBUtils, cosi' la regola sulle esclusioni e' una
sola per tutti i progetti. Qui restano soltanto i nomi di Dadillo.

Oltre alle cartelle dei dati dell'utente, che la funzione salta da se',
si lasciano fuori i materiali, l'archivio dei discepoli, le impostazioni
e le copie dei file danneggiati: nascono provando l'eseguibile prima di
comprimere.
"""

import sys

from GBUtils import crea_archivio_release

FUORI = [
    "materiali/",
    "dadillo.json",
    "dadillo_settings.json",
    "dadillo_players.json",
    "giocatori.txt",
    "*.danneggiato_*",
]


def main():
    try:
        crea_archivio_release("Dadillo", escludi=FUORI)
    except (FileNotFoundError, OSError) as e:
        print(f"Archivio non creato: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
