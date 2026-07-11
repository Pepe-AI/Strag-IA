"""Config loader (Fase 8): env → objeto Config. Puro y testeable con un env falso."""

from app.config import cargar_config
from app.google_clients import SCOPES_SA, SCOPE_OAUTH


def test_cargar_config_completo():
    env = {
        "GOOGLE_SERVICE_ACCOUNT_JSON": '{"type":"service_account","client_email":"x@y.iam"}',
        "OAUTH_CLIENT_ID": "cid",
        "OAUTH_CLIENT_SECRET": "csec",
        "OAUTH_REFRESH_TOKEN": "rtok",
        "INPUT_FOLDER_ID": "FIN",
        "RESULTS_FOLDER_ID": "FRES",
        "GEMINI_API_KEY": "gk",
        "GEMINI_MODEL": "gemini-2.5-pro",
        "WEBHOOK_SECRET": "sec",
        "RATE_MAX": "5",
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "u@g.com",
        "SMTP_PASS": "pw",
        "ALERT_EMAIL_FROM": "u@g.com",
        "ALERT_EMAIL_TO": "to@x.com",
    }
    cfg = cargar_config(env)

    assert cfg.service_account_info["client_email"] == "x@y.iam"
    assert cfg.oauth_client_id == "cid"
    assert cfg.oauth_client_secret == "csec"
    assert cfg.oauth_refresh_token == "rtok"
    assert cfg.input_folder_id == "FIN"
    assert cfg.results_folder_id == "FRES"
    assert cfg.gemini_api_key == "gk"
    assert cfg.gemini_model == "gemini-2.5-pro"
    assert cfg.webhook_secret == "sec"
    assert cfg.rate_max == 5
    assert cfg.email is not None
    assert cfg.email.host == "smtp.gmail.com"
    assert cfg.email.email_to == "to@x.com"


def test_cargar_config_sin_smtp_deja_email_none_y_modelo_por_defecto():
    cfg = cargar_config({"WEBHOOK_SECRET": "s"})
    assert cfg.email is None
    assert cfg.gemini_model == "gemini-2.5-flash"
    assert cfg.rate_max == 10  # default


def test_scopes_de_minimo_privilegio():
    # SA: solo lectura (Sheet + allowlist). OAuth-user: solo crear/subir (drive.file).
    assert set(SCOPES_SA) == {
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    }
    assert set(SCOPE_OAUTH) == {"https://www.googleapis.com/auth/drive.file"}
