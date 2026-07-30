import os
import zipfile

dist_dir = os.path.join("dist", "Dadillo")
zip_path = "Dadillo.zip"

if os.path.exists(dist_dir):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zipf.write(file_path, arcname)
    print(f"Created {zip_path} successfully.")
else:
    print(f"Directory {dist_dir} not found.")
