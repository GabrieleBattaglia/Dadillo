"""Crea l'archivio zip della cartella dist per la pubblicazione della release.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA, Claude Opus 5 in modalita' auto.
"""

import os
import zipfile

# I percorsi partono dalla cartella dello script, non dalla directory di lavoro
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(BASE_DIR, "dist", "Dadillo")
zip_path = os.path.join(BASE_DIR, "Dadillo.zip")

if os.path.exists(dist_dir):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zipf.write(file_path, arcname)
    print(f"Creato {zip_path}.")
else:
    print(f"Cartella {dist_dir} non trovata.")
