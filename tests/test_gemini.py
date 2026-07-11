"""Cliente Gemini (Fase 8). Se prueba la LÓGICA del wrapper con un client falso;
el SDK real (google-genai) no se toca en el test."""

from app.gemini import ClienteGemini


class FakeResp:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, resp, captura):
        self._resp = resp
        self._captura = captura

    def generate_content(self, model, contents, config):
        self._captura.update(model=model, contents=contents, config=config)
        return self._resp


class FakeClient:
    def __init__(self, resp, captura):
        self.models = FakeModels(resp, captura)


def test_generar_llama_al_modelo_con_json_y_baja_temperatura():
    captura = {}
    client = FakeClient(FakeResp('{"debilidades": []}'), captura)
    cg = ClienteGemini(client, model="gemini-x", temperature=0.15)

    out = cg.generar("mi prompt")

    assert out == '{"debilidades": []}'
    assert captura["model"] == "gemini-x"
    assert captura["contents"] == "mi prompt"
    assert captura["config"]["temperature"] == 0.15
    assert captura["config"]["response_mime_type"] == "application/json"


def test_cumple_la_interfaz_clienteia():
    cg = ClienteGemini(FakeClient(FakeResp("texto"), {}))
    assert cg.generar("p") == "texto"  # generar(str) -> str
