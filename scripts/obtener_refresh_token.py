"""One-time: consentimiento OAuth (Desktop) → refresh token para OAuth-as-user.

Uso:
    uv run python scripts/obtener_refresh_token.py <client_secret.json> <salida.json>

Abre el navegador; inicia sesión con la cuenta DUEÑA del Drive y autoriza el scope
drive.file. Guarda client_id/secret/refresh_token en <salida> (fuera del repo).
"""

import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def main(client_secret_path: str, salida: str) -> None:
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes=SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    datos = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
    }
    with open(salida, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, indent=2)

    print("OK — consentimiento completado")
    print("client_id:", creds.client_id)
    print("refresh_token capturado:", "SI" if creds.refresh_token else "NO")
    print("guardado en:", salida)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
