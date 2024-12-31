"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import json

import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Max, F
from django.utils import timezone
from pytz import timezone as pytz_timezone

from apps.inicio.formularios.anio import FormAnio
from apps.inicio.formularios.cargo import FormCargo
from apps.inicio.formularios.departamento import FormDepartamento
from apps.inicio.formularios.distrito import FormDistrito
from apps.inicio.formularios.pais import FormPais
from apps.inicio.formularios.provincia import FormProvincia
from apps.inicio.formularios.tipodocumentoidentidad import FormTipoDocumentoIdentidad
from apps.inicio.formularios.tipofirma import FormTipoFirma
from apps.inicio.formularios.tipotramite import FormTipoTramite
from apps.inicio.models import Pais, Departamento, Provincia, Distrito, Cargo, TipoDocumentoIdentidad, TipoFirma, Anio
from apps.inicio.vistas.nucleo import ObtenerTokenNucleo
from apps.organizacion.formularios.areatipo import FormAreaTipo
from apps.organizacion.formularios.dependencia import FormDependencia
from apps.organizacion.formularios.documentotipo import FormDocumentoTipo
from apps.organizacion.models import AreaTipo, Area, Dependencia
from apps.tramite.formularios.documentotipoplantilla import FormDocumentoTipoPlantilla
from apps.tramite.formularios.tipoproveido import FormTipoProveido
from apps.tramite.models import DocumentoTipo, DocumentoTipoPlantilla, TipoTramite, TipoProveido
from madceropapel.celery import app
from modulos.utiles.clases.varios import maximo

logger = get_task_logger(__name__)


def format_fecha(fecha):
    return None if not fecha else timezone.make_aware(timezone.now().strptime(fecha, "%d/%m/%Y %H:%M:%S"))


def verificador(Modelo, Formulario, urlconsulta, token):
    fechamaxima = maximo([
        Modelo.objects.aggregate(fecha=Max("creado"))["fecha"],
        Modelo.objects.aggregate(fecha=Max("actualizado"))["fecha"],
        timezone.make_aware(timezone.now().strptime("01/01/1900", "%d/%m/%Y"))
    ])
    urlmodelo = urlconsulta % fechamaxima.astimezone(tz=pytz_timezone(settings.TIME_ZONE)).strftime("%Y%m%d%H%M%S")
    r = requests.post(
        urlmodelo,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Token " + token
        }
    )
    if r.ok:
        resultado = json.loads(r.text)
        for regnuevo in resultado:
            registro = Modelo.objects.filter(pk=regnuevo["id"]).first()
            formulario = Formulario(data=regnuevo, instance=registro)
            if formulario.is_valid():
                if registro:
                    formulario.instance.editor_id = 1
                else:
                    formulario.instance.creador_id = 1
                formulario.save()
                registro = Modelo.objects.filter(pk=formulario.instance.pk).first()
                registro.creado = format_fecha(regnuevo["creado"])
                registro.actualizado = format_fecha(regnuevo["actualizado"])
                registro.save()
            else:
                print(formulario.errors)


@app.task(name="ini.verifica_maestros", ignore_result=True)
def verifica_maestros():
    urlnucleo = settings.CONFIG_APP["NUCLEO"]["URL"]
    # try:
    token = ObtenerTokenNucleo()
    verificador(Anio, FormAnio, urlnucleo + "/inicio/anios/validar/%s", token)
    verificador(Pais, FormPais, urlnucleo + "/inicio/paises/validar/%s", token)
    verificador(Departamento, FormDepartamento, urlnucleo + "/inicio/departamentos/validar/%s", token)
    verificador(Provincia, FormProvincia, urlnucleo + "/inicio/provincias/validar/%s", token)
    verificador(Distrito, FormDistrito, urlnucleo + "/inicio/distritos/validar/%s", token)
    verificador(Cargo, FormCargo, urlnucleo + "/inicio/cargos/validar/%s", token)
    verificador(
        TipoDocumentoIdentidad, FormTipoDocumentoIdentidad, urlnucleo + "/inicio/tipodocumentoidentidades/validar/%s",
        token
    )
    verificador(TipoFirma, FormTipoFirma, urlnucleo + "/inicio/tipofirmas/validar/%s", token)
    verificador(TipoTramite, FormTipoTramite, urlnucleo + "/inicio/tipotramites/validar/%s", token)
    verificador(TipoProveido, FormTipoProveido, urlnucleo + "/inicio/tipoproveidos/validar/%s", token)
    verificador(DocumentoTipo, FormDocumentoTipo, urlnucleo + "/organizacion/documentotipos/validar/%s", token)
    verificador(AreaTipo, FormAreaTipo, urlnucleo + "/organizacion/areatipos/validar/%s", token)
    verificador(Dependencia, FormDependencia, urlnucleo + "/organizacion/dependencia/validar/%s", token)
    # ===================
    # DocumentoTipoPlantilla
    fechamaxima = maximo([
        DocumentoTipoPlantilla.objects.aggregate(fecha=Max("creado"))["fecha"],
        DocumentoTipoPlantilla.objects.aggregate(fecha=Max("actualizado"))["fecha"],
        timezone.make_aware(timezone.now().strptime("01/01/1900", "%d/%m/%Y"))
    ])
    urlconsulta = urlnucleo + "/organizacion/documentotipoplantillas/validar/%s/%s"
    urlmodelo = urlconsulta % (
        settings.CONFIG_APP["Dependencia"],
        fechamaxima.astimezone(tz=pytz_timezone(settings.TIME_ZONE)).strftime("%Y%m%d%H%M%S")
    )
    r = requests.post(
        urlmodelo,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Token " + token
        }
    )
    if r.ok:
        resultado = json.loads(r.text)
        for regnuevo in resultado:
            regnuevo.update({"archivof": regnuevo["archivo"], "archivo": None})
            regnuevo.update({"archivoc": regnuevo["archivoparacontenido"], "archivoparacontenido": None})
            regnuevo.update({"archivop": regnuevo["archivoposfirma"], "archivoposfirma": None})
            registro = DocumentoTipoPlantilla.objects.filter(
                dependencia_id=regnuevo["dependencia"],
                documentotipo_id=regnuevo["documentotipo"]
            ).first()
            formulario = FormDocumentoTipoPlantilla(data=regnuevo, instance=registro)
            if formulario.is_valid():
                if registro:
                    formulario.instance.editor_id = 1
                else:
                    formulario.instance.creador_id = 1
                formulario.save()
                registro = DocumentoTipoPlantilla.objects.filter(pk=formulario.instance.pk).first()
                registro.creado = format_fecha(regnuevo["creado"])
                registro.actualizado = format_fecha(regnuevo["actualizado"])
                registro.save()
            else:
                print(formulario.errors)


@app.task(name="ini.carga_areas", ignore_result=True)
def carga_areas():
    token = ObtenerTokenNucleo()
    datasubir = Area.objects.filter(
        modificado=True,
        dependencia__codigo=settings.CONFIG_APP["Dependencia"],
        paracomisiones=False
    ).order_by(
        "actualizado"
    ).annotate(
        dependenciacodigo=F("dependencia__codigo"),
        padrecodigo=F("padre__codigo"),
        areatipoid=F("areatipo_id"),
        jefeactualdni=F("jefeactual__persona__numero"),
        jefecargoid=F("jefeactual__cargo_id")
    ).values(
        "codigo",
        "dependenciacodigo",
        "padrecodigo",
        "orden",
        "nombre",
        "nombrecorto",
        "siglas",
        "areatipoid",
        "paracomisiones",
        "activo",
        "jefeactualdni",
        "jefecargoid"
    )
    if datasubir.count() > 0:
        datasubirf = list(datasubir)
        urlsubir = "%s%s" % (
            settings.CONFIG_APP["NUCLEO"]["URL"],
            settings.CONFIG_APP["NUCLEO"]["MAD3"]["areas"]["subir"]
        )
        try:
            r = requests.post(
                urlsubir,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Token " + token
                },
                json=datasubirf
            )
            if r.ok:
                datasubir.update(modificado=False)
        except Exception as e:
            pass
