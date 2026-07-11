"""Primitivas de seguridad (Fase 5).

Defensa en profundidad: el secreto dice *quién* llama; el allowlist dice *qué* Sheet
puede procesarse. Todo puro/inyectable para probar sin red.
"""

import secrets
import time
from collections import deque
from collections.abc import Callable


def validar_secreto(recibido: str, esperado: str) -> bool:
    """Comparación en tiempo constante. Deniega si no hay secreto configurado."""
    if not esperado or not recibido:
        return False
    return secrets.compare_digest(recibido, esperado)


class RateLimiter:
    """Ventana deslizante simple, en memoria (single-tenant, bajo volumen).

    `reloj` es inyectable para poder probar sin esperar tiempo real.
    """

    def __init__(
        self,
        max_solicitudes: int,
        ventana_seg: float = 60.0,
        reloj: Callable[[], float] = time.monotonic,
    ):
        self.max = max_solicitudes
        self.ventana = ventana_seg
        self.reloj = reloj
        self._hits: dict[str, deque] = {}

    def permitir(self, clave: str) -> bool:
        ahora = self.reloj()
        dq = self._hits.setdefault(clave, deque())
        while dq and dq[0] <= ahora - self.ventana:
            dq.popleft()
        if len(dq) >= self.max:
            return False
        dq.append(ahora)
        return True


def sheet_en_carpeta(sheet_id: str, service, folder_id: str) -> bool:
    """True si el Sheet está dentro de la carpeta autorizada.

    Usa `files.get(fileId, fields="parents")` (scope drive.metadata.readonly). Un
    secreto filtrado no basta para procesar Sheets arbitrarios (ARCHITECTURE §5).
    """
    meta = service.files().get(fileId=sheet_id, fields="parents").execute()
    parents = meta.get("parents") or []
    return folder_id in parents
