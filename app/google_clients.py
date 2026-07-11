"""Construcción de los clientes reales de Google (Fase 8) — auth híbrida.

- Cuenta de servicio (SA): lee el Sheet + allowlist (no puede ESCRIBIR en un Drive
  personal — verificado: 403 sin storage).
- OAuth-as-user: sube el PDF con `drive.file` (queda a nombre del usuario, usa su
  storage). Scope no sensible → sin verificación de Google.

Imports perezosos para no cargar el SDK salvo en uso.
"""

SCOPES_SA = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",  # leer el Sheet
    "https://www.googleapis.com/auth/drive.metadata.readonly",  # allowlist (parents)
]
SCOPE_OAUTH = ["https://www.googleapis.com/auth/drive.file"]  # subir el PDF

_TOKEN_URI = "https://oauth2.googleapis.com/token"


def construir_credenciales_sa(service_account_info: dict, scopes=SCOPES_SA):
    from google.oauth2 import service_account

    return service_account.Credentials.from_service_account_info(
        service_account_info, scopes=scopes
    )


def construir_credenciales_usuario(client_id: str, client_secret: str, refresh_token: str):
    from google.oauth2.credentials import Credentials

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri=_TOKEN_URI,
        scopes=SCOPE_OAUTH,
    )


def construir_sheets(credenciales):
    from googleapiclient.discovery import build

    return build("sheets", "v4", credentials=credenciales, cache_discovery=False)


def construir_drive(credenciales):
    from googleapiclient.discovery import build

    return build("drive", "v3", credentials=credenciales, cache_discovery=False)
