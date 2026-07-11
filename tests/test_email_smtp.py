"""Envío de email de alerta por SMTP (Fase 8, sin credenciales para escribirse).

`smtplib.SMTP` se inyecta como factory → se prueba el flujo (starttls/login/send)
sin red ni cuenta real.
"""

from app.email_smtp import EmailConfig, crear_enviador, enviar_email_smtp

CFG = EmailConfig(
    host="smtp.gmail.com",
    port=587,
    user="remitente@gmail.com",
    password="app-pass",
    email_from="remitente@gmail.com",
    email_to="alertas@empresa.com",
)


class FakeSMTP:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.acciones = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.acciones.append(("close",))

    def starttls(self):
        self.acciones.append(("starttls",))

    def login(self, u, p):
        self.acciones.append(("login", u, p))

    def send_message(self, msg):
        self.acciones.append(("send", msg))


def test_enviar_email_smtp_hace_starttls_login_y_send():
    creados = []

    def factory(host, port):
        s = FakeSMTP(host, port)
        creados.append(s)
        return s

    enviar_email_smtp(CFG, "run9", ValueError("boom"), smtp_factory=factory)

    s = creados[0]
    assert (s.host, s.port) == ("smtp.gmail.com", 587)
    assert [a[0] for a in s.acciones] == ["starttls", "login", "send", "close"]

    login = next(a for a in s.acciones if a[0] == "login")
    assert login[1:] == ("remitente@gmail.com", "app-pass")

    msg = next(a for a in s.acciones if a[0] == "send")[1]
    assert msg["To"] == "alertas@empresa.com"
    assert msg["From"] == "remitente@gmail.com"
    assert "run9" in msg["Subject"]
    assert "boom" in msg.get_content()


def test_crear_enviador_devuelve_callable_compatible_con_ejecutar_corrida():
    enviados = []

    def factory(host, port):
        s = FakeSMTP(host, port)
        enviados.append(s)
        return s

    enviar = crear_enviador(CFG, smtp_factory=factory)
    enviar("run10", RuntimeError("x"))  # firma (run_id, error)

    assert enviados and any(a[0] == "send" for a in enviados[0].acciones)
