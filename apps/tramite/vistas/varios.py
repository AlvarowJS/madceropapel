"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import json

import requests
from django.conf import settings
from django.core.validators import validate_email
from django.utils import timezone

from apps.inicio.formularios.persona import FormPersona
from apps.inicio.formularios.personajuridica import FormPersonaJuridica
from apps.inicio.models import PersonaJuridica, Persona, TipoDocumentoIdentidad, Pais
from apps.inicio.vistas.nucleo import ObtenerTokenNucleo


def ConsultarRUC(ruc, request):
    pj = PersonaJuridica.objects.filter(ruc=ruc)
    estado = None
    personajuridica = pj.first()
    if not personajuridica or not personajuridica.consultaruc:
        try:
            urlnucleo = settings.CONFIG_APP["NUCLEO"]["URL"]
            token = ObtenerTokenNucleo()
            #
            urlruc = "%s/personal/consulta/ruc/%s" % (
                urlnucleo,
                ruc
            )
            r = requests.post(
                urlruc,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Token " + token
                }
            )
            resultruc = json.loads(r.text)
            if resultruc["success"]:
                if resultruc["correo"]:
                    correo = str(resultruc["correo"])
                    sep = ""
                    if correo.__contains__(","):
                        sep = ","
                    elif correo.__contains__("/"):
                        sep = "/"
                    if len(sep) > 0:
                        correo = correo.split(sep)[0].strip()
                    correo = correo.replace(":", "").strip()
                    correo = correo.replace("á", "a").strip()
                    correo = correo.replace("é", "e").strip()
                    correo = correo.replace("í", "i").strip()
                    correo = correo.replace("ó", "o").strip()
                    correo = correo.replace("ú", "u").strip()
                    try:
                        validate_email(correo)
                    except:
                        correo = None
                    resultruc["correo"] = correo
                pjf = FormPersonaJuridica(data=resultruc, instance=personajuridica)
                if pjf.is_valid():
                    if not personajuridica:
                        pjf.instance.creador = request.user
                    else:
                        pjf.instance.editor = request.user
                    pjf.instance.consultaruc = timezone.now().date()
                    pjf.save()
                    personajuridica = PersonaJuridica.objects.filter(ruc=ruc).first()
                else:
                    print("ERROR", pjf.errors)
            else:
                # estado = "No se pudo realizar la consulta, intente nuevamente"
                estado = resultruc["msgerror"]
        except Exception as e:
            estado = "No se pudo realizar la consulta, intente nuevamente"
    return personajuridica, estado


def ConsultarDNI(dni, request):
    per = Persona.objects.filter(tipodocumentoidentidad__codigo="DNI", numero=dni).first()
    estado = None
    if not per or not per.consultadni:
        urlnucleo = settings.CONFIG_APP["NUCLEO"]["URL"]
        # try:
        token = ObtenerTokenNucleo()
        #
        urldni = "%s/personal/consulta/dni/%s" % (
            urlnucleo,
            dni
        )
        r = requests.post(
            urldni,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Token " + token
            }
        )
        if r.ok:
            resultdni = json.loads(r.text)
            if resultdni["success"]:
                resultdni["tipodocumentoidentidad"] = TipoDocumentoIdentidad.objects.get(codigo="DNI")
                resultdni["pais"] = Pais.objects.get(nombre="PERU")
                resultdni["consultadni"] = validacion(resultdni["validacion"])
                resultdni["foto"] = resultdni["fotografia"]
                perf = FormPersona(data=resultdni, instance=per)
                if perf.is_valid():
                    perf.instance.ubigeo_id = resultdni["ubigeo_id"]
                    perf.instance.creador = request.user
                    try:
                        perf.save()
                        per = perf.instance
                    except Exception as e:
                        # print(e)
                        estado = str(e)
                else:
                    # print(perf.errors)
                    target = list(perf.errors) + list(perf.errors.values())
                    estado = ' '.join([l for l in target])
            else:
                estado = "Error de consulta"
        else:
            estado = r.text
        # except Exception as e:
            # print(e)
            # estado = str(e)
            # estado = "No se pudo realizar la consulta. Intente nuevamente."
    if per:
        estado = None
    return per, estado


def validacion(fecha):
    _result = None
    if fecha:
        _result = timezone.make_aware(timezone.now().strptime(fecha, "%Y-%m-%d %H:%M:%S"))
    return _result
