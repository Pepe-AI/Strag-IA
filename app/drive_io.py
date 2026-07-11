"""IO de Google Drive (Fase 6).

Sube el PDF a la carpeta de resultados (propiedad de la cuenta de servicio → scope
`drive.file`). Idempotencia SIN mutar el Sheet: el PDF se nombra de forma
determinista y un re-run **sobrescribe** el mismo archivo (ARCHITECTURE §9, ADR-3).

El `service` se inyecta (construido en la Fase 8). `media_factory` aísla
google-api-python-client para poder probar sin esa dependencia ni red.
"""

import re


def nombre_pdf(empresa: str, fecha: str) -> str:
    """Nombre determinista `<empresa>_<fecha>.pdf` (saneado para Drive)."""

    def limpio(s: str) -> str:
        return re.sub(r"[^\w.-]+", "_", s.strip()).strip("_")

    return f"{limpio(empresa)}_{limpio(fecha)}.pdf"


def _media_por_defecto(pdf_bytes: bytes):
    import io

    from googleapiclient.http import MediaIoBaseUpload

    return MediaIoBaseUpload(
        io.BytesIO(pdf_bytes), mimetype="application/pdf", resumable=False
    )


def subir_pdf(
    service,
    folder_id: str,
    nombre: str,
    pdf_bytes: bytes,
    media_factory=_media_por_defecto,
) -> dict:
    """Crea el PDF en la carpeta, o lo sobrescribe si ya existe uno con ese nombre."""
    media = media_factory(pdf_bytes)
    q = f"name = '{nombre}' and '{folder_id}' in parents and trashed = false"
    existentes = (
        service.files().list(q=q, fields="files(id,name)").execute().get("files", [])
    )
    if existentes:
        file_id = existentes[0]["id"]
        return (
            service.files()
            .update(fileId=file_id, media_body=media, fields="id")
            .execute()
        )
    body = {"name": nombre, "parents": [folder_id]}
    return service.files().create(body=body, media_body=media, fields="id").execute()
