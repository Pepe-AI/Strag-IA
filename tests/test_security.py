"""Primitivas de seguridad (Fase 5), puras y testeables sin red."""

from app.security import RateLimiter, sheet_en_carpeta, validar_secreto


# --- secreto compartido ---

def test_secreto_correcto():
    assert validar_secreto("abc123", "abc123") is True


def test_secreto_incorrecto():
    assert validar_secreto("malo", "abc123") is False


def test_secreto_vacio_o_faltante_es_invalido():
    assert validar_secreto("", "abc123") is False
    assert validar_secreto("abc123", "") is False  # sin secreto configurado → deniega


# --- rate limiter (reloj inyectable) ---

class _Reloj:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_rate_limiter_permite_hasta_el_maximo_y_luego_bloquea():
    reloj = _Reloj()
    rl = RateLimiter(max_solicitudes=2, ventana_seg=60, reloj=reloj)
    assert rl.permitir("ip") is True
    assert rl.permitir("ip") is True
    assert rl.permitir("ip") is False  # 3ra en la ventana → bloqueada


def test_rate_limiter_se_recupera_al_pasar_la_ventana():
    reloj = _Reloj()
    rl = RateLimiter(max_solicitudes=1, ventana_seg=60, reloj=reloj)
    assert rl.permitir("ip") is True
    assert rl.permitir("ip") is False
    reloj.t = 61
    assert rl.permitir("ip") is True


# --- allowlist por carpeta de Drive ---

class FakeDrive:
    """Imita service.files().get(fileId=..., fields=...).execute()."""

    def __init__(self, parents):
        self._parents = parents
        self.captured = {}

    def files(self):
        return self

    def get(self, fileId, fields):
        self.captured = {"fileId": fileId, "fields": fields}
        return self

    def execute(self):
        return {"parents": self._parents}


def test_sheet_dentro_de_carpeta_autorizada():
    drive = FakeDrive(["FOLDER_OK", "otro"])
    assert sheet_en_carpeta("SHEET1", drive, "FOLDER_OK") is True
    assert drive.captured["fileId"] == "SHEET1"


def test_sheet_fuera_de_carpeta_no_autorizado():
    assert sheet_en_carpeta("SHEET1", FakeDrive(["otra_carpeta"]), "FOLDER_OK") is False


def test_sheet_sin_parents_no_autorizado():
    assert sheet_en_carpeta("SHEET1", FakeDrive(None), "FOLDER_OK") is False
