"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import base64
import json

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, generics, serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.inicio.models import Distrito
from apps.organizacion.models import DocumentoTipoArea, Area
from apps.tramite.models import Documento, DocumentoEstado, Destino, DestinoEstado, DocumentoPDF, TipoTramite, \
    TipoProveido, MensajeriaModoEntrega
from apps.tramite.vistas.varios import ConsultarRUC, ConsultarDNI


class RegistroAgregarSerializer(serializers.ModelSerializer):
    documentotipo = serializers.CharField(max_length=3)
    numero = serializers.IntegerField()
    emisorruc = serializers.CharField(max_length=11, required=False, allow_null=True)
    emisordni = serializers.CharField(max_length=8, required=False)
    emisorcargo = serializers.CharField(max_length=150, required=False)
    tramitadordni = serializers.CharField(max_length=8, required=False, allow_null=True)
    ubigeocodigo = serializers.CharField(max_length=6)
    archivointerno = serializers.CharField()
    destinos = serializers.CharField()

    class Meta:
        model = Documento
        fields = [
            "origentipo", "documentotipo", "numero", "siglas", "folios",
            "asunto", "fecha", "areavirtualdestino",
            "emisorruc", "emisordni", "emisorcargo", "tramitadordni",
            "correo", "telefono", "ubigeocodigo", "direccion", "archivointerno",
            "archivoexterno", "destinos"
        ]

    def setRequest(self, request):
        self.request = request

    def getRequest(self):
        return self.request

    def create(self, validated_data):
        _notodo_ok = False
        periodoactual = self.request.user.persona.periodotrabajoactual()
        # print(periodoactual)
        # Buscamos el tipo de documento
        dta = DocumentoTipoArea.objects.filter(
            area=periodoactual.area,
            documentotipo__codigo=validated_data["documentotipo"]
        ).first()
        if dta:
            validated_data["documentotipoarea_id"] = dta.pk
        else:
            raise ValidationError("El tipo de documento no está asignado al área")
        validated_data["anio"] = timezone.now().year
        validated_data["emisor_id"] = periodoactual.pk
        validated_data["remitentetipo"] = "J" if validated_data.get("emisorruc") else "C"
        if validated_data.get("emisorruc"):
            pj, estado = ConsultarRUC(validated_data.get("emisorruc"), self.request)
            if estado:
                _notodo_ok = estado
            else:
                validated_data["personajuridicatipo"] = "R"
                validated_data["personajuridica_id"] = pj.pk
        if validated_data.get("emisordni"):
            per, estado = ConsultarDNI(validated_data.get("emisordni"), self.request)
            if estado:
                _notodo_ok = estado
            else:
                validated_data["ciudadanoemisor_id"] = per.pk
            del validated_data["emisordni"]
        if validated_data.get("emisorcargo"):
            validated_data["ciudadanocargo"] = validated_data.get("emisorcargo")
            del validated_data["emisorcargo"]
        if validated_data.get("tramitadordni"):
            per, estado = ConsultarDNI(validated_data.get("tramitadordni"), self.request)
            if estado:
                _notodo_ok = estado
            else:
                validated_data["ciudadanotramitador_id"] = per.pk
        if _notodo_ok:
            raise ValidationError(_notodo_ok)
        else:
            validated_data["distrito_id"] = Distrito.objects.filter(codigo=validated_data["ubigeocodigo"]).first().pk
            validated_data["verificado"] = True
            validated_data["creador_id"] = self.request.user.pk
            validated_data["editor_id"] = self.request.user.pk
            #
            del validated_data["documentotipo"]
            del validated_data["emisorruc"]
            del validated_data["ubigeocodigo"]
            del validated_data["archivointerno"]
            del validated_data["destinos"]
            del validated_data["tramitadordni"]
            return super(RegistroAgregarSerializer, self).create(validated_data)


class RegistroUOSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField("fnombre")
    class Meta:
        model = Area
        fields = [
            "nombre", "id"
        ]

    def fnombre(self, area):
        return "%s - %s" % (
            area.nombre,
            area.siglas
        )


class RegistroUOListar(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"
    serializer_class = RegistroUOSerializer
    queryset = Area.objects.all()

    def get_queryset(self):
        qs = super(RegistroUOListar, self).get_queryset()
        qs = qs.filter(
            activo=True
        ).order_by("nombre")
        periodoactual = self.request.user.persona.periodotrabajoactual()
        area = periodoactual.area
        if area.rindentepadre:
            area = area.rindentepadre
        if area.esrindente:
            qs = qs.filter(
                Q(pk=area.pk)
                |
                Q(rindentepadre_id=area.pk)
            )
        else:
            qs = qs.filter(
                Q(rindentepadre__isnull=True)
                |
                Q(paracomisiones=True)
            )
        return qs

    def post(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RegistroAgregar(generics.CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = "post"
    serializer_class = RegistroAgregarSerializer
    queryset = Documento.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.setRequest(request=request)
        valido = serializer.is_valid(raise_exception=False)
        if valido:
            doc = serializer.save()
            #
            documentoestado = DocumentoEstado.objects.create(
                documento=doc,
                estado="EM",
                creador=request.user
            )
            doc.ultimoestado = documentoestado
            doc.estadoemitido = documentoestado
            doc.save()
            primerdestino = None
            destinos = json.loads(request.data["destinos"])
            for idx, destino in enumerate(destinos):
                coddes = int(destino["destino"])
                ofides = Area.objects.get(pk=coddes)
                periodotrabajo = ofides.jefeactual
                if not periodotrabajo:
                    ofides.TrabajadoresActuales().first()
                destinoreg = Destino.objects.create(
                    documento=doc,
                    tipodestinatario="UO",
                    periodotrabajo=periodotrabajo,
                    tipotramite=TipoTramite.objects.get(codigo='0'),
                    proveido=TipoProveido.objects.get(pk=1),
                    mensajeriamodoentrega=MensajeriaModoEntrega.objects.get(codigo="MG"),
                    indicacion=destino["proveido"],
                    creador=request.user
                )
                DestinoEstado.objects.create(
                    destino=destinoreg,
                    estado="NL",
                    creador=request.user
                )
                if not primerdestino:
                    primerdestino = destinoreg
            documentobinary = base64.b64decode(request.data["archivointerno"])
            docplla = doc.documentoplantilla
            docplla.contenido = documentobinary
            docplla.save()
            if doc.documentotipoarea.documentotipo.esmultiple:
                for idx, destino in enumerate(destinos):
                    coddes = int(destino["destino"])
                    ofides = Area.objects.get(pk=coddes)
                    DocumentoPDF.objects.create(
                        documentoplantilla=docplla,
                        destino=doc.des_documento.filter(periodotrabajo__area=ofides).first(),
                        pdf=documentobinary,
                        estado="G",
                        creador=request.user
                    )
            else:
                DocumentoPDF.objects.create(
                    documentoplantilla=docplla,
                    destino=primerdestino,
                    pdf=documentobinary,
                    estado="G",
                    creador=request.user
                )
            #
            dataresult = {
                "numero": doc.expediente.numero,
                "anio": doc.expediente.anio,
                "codep": doc.expediente.dependencia.codigo,
                "clave": doc.clave
            }
            headers = self.get_success_headers(dataresult)
            return Response(dataresult, status=status.HTTP_201_CREATED, headers=headers)
        else:
            dataResult = {
                "success": False,
                "errors": serializer.errors.__str__()
            }
            return Response(dataResult, status=status.HTTP_206_PARTIAL_CONTENT)
