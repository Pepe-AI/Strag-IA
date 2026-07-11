"""Crea (una vez) la subcarpeta `resultados` dentro de la carpeta de entrada, a
nombre de la cuenta de servicio, y muestra su ID (→ RESULTS_FOLDER_ID).

Uso:
    uv run python scripts/crear_carpeta_resultados.py <ruta_json_SA> <INPUT_FOLDER_ID>

Verifica en vivo si `drive.file` puede escribir en la carpeta compartida.
"""

import json
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main(sa_path: str, input_folder_id: str) -> None:
    with open(sa_path, encoding="utf-8") as fh:
        info = json.load(fh)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    # Diagnóstico: ¿la SA ve la carpeta compartida con scope 'drive'?
    carpeta = drive.files().get(fileId=input_folder_id, fields="id,name").execute()
    print("Carpeta visible:", carpeta)

    meta = {
        "name": "resultados",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [input_folder_id],
    }
    folder = drive.files().create(body=meta, fields="id,name,parents").execute()
    print("OK — carpeta creada")
    print("RESULTS_FOLDER_ID:", folder["id"])
    print("parents:", folder.get("parents"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
