"""Config loader (Fase 8): variables de entorno → objeto `Config`.

Puro (recibe un `env` dict) para poder probarse sin tocar el entorno real.
"""

import json
import os
from collections.abc import Mapping

from pydantic import BaseModel

from app.email_smtp import EmailConfig


class Config(BaseModel):
    service_account_info: dict  # SA: lee el Sheet + allowlist
    oauth_client_id: str  # OAuth-as-user: sube el PDF
    oauth_client_secret: str
    oauth_refresh_token: str
    input_folder_id: str
    results_folder_id: str
    gemini_api_key: str
    gemini_model: str
    webhook_secret: str
    rate_max: int
    email: EmailConfig | None


def cargar_config(env: Mapping[str, str] | None = None) -> Config:
    env = os.environ if env is None else env

    sa_raw = env.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    service_account_info = json.loads(sa_raw) if sa_raw else {}

    email = None
    if env.get("SMTP_HOST"):
        email = EmailConfig(
            host=env["SMTP_HOST"],
            port=int(env.get("SMTP_PORT", "587")),
            user=env.get("SMTP_USER", ""),
            password=env.get("SMTP_PASS", ""),
            email_from=env.get("ALERT_EMAIL_FROM", ""),
            email_to=env.get("ALERT_EMAIL_TO", ""),
        )

    return Config(
        service_account_info=service_account_info,
        oauth_client_id=env.get("OAUTH_CLIENT_ID", ""),
        oauth_client_secret=env.get("OAUTH_CLIENT_SECRET", ""),
        oauth_refresh_token=env.get("OAUTH_REFRESH_TOKEN", ""),
        input_folder_id=env.get("INPUT_FOLDER_ID", ""),
        results_folder_id=env.get("RESULTS_FOLDER_ID", ""),
        gemini_api_key=env.get("GEMINI_API_KEY", ""),
        gemini_model=env.get("GEMINI_MODEL", "gemini-2.5-flash"),
        webhook_secret=env.get("WEBHOOK_SECRET", ""),
        rate_max=int(env.get("RATE_MAX", "10")),
        email=email,
    )
