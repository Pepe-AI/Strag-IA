"""Cliente Gemini real (Fase 8), detrás de la interfaz `ClienteIA`.

Una llamada, baja temperatura, salida forzada a JSON (`response_mime_type`). El
`client` del SDK se inyecta para poder probar sin red; la validación de la salida
la sigue haciendo `app.hallazgos.validar_salida`.
"""

DEFAULT_MODEL = "gemini-2.5-flash"


class ClienteGemini:
    """Cumple `ClienteIA`: `generar(prompt) -> str`."""

    def __init__(self, client, model: str = DEFAULT_MODEL, temperature: float = 0.2):
        self._client = client
        self._model = model
        self._temperature = temperature

    def generar(self, prompt: str) -> str:
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config={
                "temperature": self._temperature,
                "response_mime_type": "application/json",
            },
        )
        return resp.text


def crear_cliente_gemini(
    api_key: str, model: str = DEFAULT_MODEL, temperature: float = 0.2
) -> ClienteGemini:
    """Construye el cliente con el SDK real (import perezoso)."""
    from google import genai

    return ClienteGemini(
        genai.Client(api_key=api_key), model=model, temperature=temperature
    )
