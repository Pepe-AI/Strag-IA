"""IO de Drive (Fase 6): nombre determinista + subida idempotente (crea/sobrescribe).

Sin red: `service` falso inyectado y `media_factory` que evita google-api-python-client.
No se muta el Sheet; la idempotencia es por nombre del PDF (ARCHITECTURE §9, ADR-3).
"""

from app.drive_io import nombre_pdf, subir_pdf


def test_nombre_pdf_determinista():
    assert nombre_pdf("VASE Sísmica", "2026-07-10") == "VASE_Sísmica_2026-07-10.pdf"


def test_nombre_pdf_sanea_caracteres_problematicos():
    assert nombre_pdf("A/B: C", "2026-07-10") == "A_B_C_2026-07-10.pdf"


class FakeDrive:
    """Imita service.files().{list,create,update}(...).execute()."""

    def __init__(self, existentes):
        self._existentes = existentes
        self.calls = []
        self._ret = None

    def files(self):
        return self

    def list(self, q, fields):
        self.calls.append(("list", q))
        self._ret = {"files": self._existentes}
        return self

    def create(self, body, media_body, fields):
        self.calls.append(("create", body, media_body))
        self._ret = {"id": "NEW_ID"}
        return self

    def update(self, fileId, media_body, fields):
        self.calls.append(("update", fileId, media_body))
        self._ret = {"id": fileId}
        return self

    def execute(self):
        return self._ret


def test_subir_pdf_crea_si_no_existe():
    drive = FakeDrive(existentes=[])
    res = subir_pdf(drive, "FOLDER", "x.pdf", b"%PDF", media_factory=lambda b: b)

    assert res["id"] == "NEW_ID"
    ops = [c[0] for c in drive.calls]
    assert "create" in ops and "update" not in ops
    create = next(c for c in drive.calls if c[0] == "create")
    assert create[1] == {"name": "x.pdf", "parents": ["FOLDER"]}
    assert create[2] == b"%PDF"  # media inyectada


def test_subir_pdf_sobrescribe_si_ya_existe():
    drive = FakeDrive(existentes=[{"id": "OLD", "name": "x.pdf"}])
    res = subir_pdf(drive, "FOLDER", "x.pdf", b"%PDF", media_factory=lambda b: b)

    assert res["id"] == "OLD"
    ops = [c[0] for c in drive.calls]
    assert "update" in ops and "create" not in ops
    update = next(c for c in drive.calls if c[0] == "update")
    assert update[1] == "OLD"
