"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings

from apps.inicio.vistas.inicio import requestsConsulta


class CorreoEnviar:
    def __init__(self, to_email, subject, body):
        self.to_email = to_email
        self.subject = subject
        self.body = body

    def enviar(self):
        ok, data = requestsConsulta(
            "%ssrv/auth" % settings.EMAIL_CONFIG["HOST"],
            settings.EMAIL_CONFIG["USER"],
            settings.EMAIL_CONFIG["PASS"]
        )
        if ok:
            requestsConsulta(
                "%ssrv/email/enviar" % settings.EMAIL_CONFIG["HOST"],
                token=data["token"],
                jsondata={
                    "desde": "TT",
                    "para": [
                        {"correo": self.to_email}
                    ],
                    "asunto": self.subject,
                    "contenido": self.body,
                    "encabezados": {"sistema": settings.CONFIG_APP["Titulo"]},
                    "etiquetas": [settings.CONFIG_APP["Titulo"]]
                }
            )


class CorreoEnviarOLD:
    def __init__(self, to_email, subject, body):
        self.to_email = to_email
        self.subject = subject
        self.body = body

    def enviar(self):
        idEmail = 0
        usuario, dominio = self.to_email.split("@")
        if dominio != settings.EMAIL_LIST[0]["DOMAIN"]:
            idEmail = 1
        from_email = settings.EMAIL_LIST[idEmail]["FROM"]
        email_context = ssl.create_default_context()
        email_message = MIMEMultipart("alternative")
        email_message["Subject"] = self.subject
        email_message["From"] = from_email
        email_message["To"] = self.to_email
        email_message.attach(MIMEText(self.body, "html"))
        with smtplib.SMTP(host=settings.EMAIL_LIST[idEmail]["HOST"], port=settings.EMAIL_LIST[idEmail]["PORT"]) \
                as email_server:
            email_server.starttls(context=email_context)
            email_server.login(user=settings.EMAIL_LIST[idEmail]["USER"], password=settings.EMAIL_LIST[idEmail]["PASS"])
            email_server.sendmail(from_email, self.to_email, email_message.as_string())
            email_server.close()
