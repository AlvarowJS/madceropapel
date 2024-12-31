"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import datetime
import io
import os.path

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic import TemplateView
from xhtml2pdf import pisa
from apps.inicio.vistas.inicio import TemplateValidaLogin
from apps.tramite.models import CargoExterno
from apps.tramite.vistas.plantillas.hojaenvio import fetch_resources
from modulos.utiles.clases.varios import formatdate, load_bytes, ConvertPica

import xlsxwriter


class MensajeriaPlanilladoVista(TemplateValidaLogin, TemplateView):
    template_name = "inicio/blanco.html"

    def render_to_response(self, context, **response_kwargs):
        cargoexterno = CargoExterno.objects.filter(pk=self.kwargs.get("pk")).first()
        como = self.request.GET.get("como")
        if cargoexterno:
            context["cargoexterno"] = cargoexterno
            if como == "pdf":
                template = get_template("tramite/plantillas/cargoexterno.html")
                tplhtml = template.render(request=self.request, context=context)
                result = io.BytesIO()
                pdf = pisa.pisaDocument(tplhtml.encode("utf-8"), dest=result, link_callback=fetch_resources)
                if not pdf.err:
                    response = HttpResponse(result.getvalue(), content_type='application/pdf; charset=utf-8')
                    response['Content-Disposition'] = 'inline; filename="Planillado%s.pdf"' % cargoexterno.NumeroFull()
                    return response
                else:
                    return HttpResponse("<div>%s</div>" % pdf.err)
            elif como == "xls":
                # filetmp = os.path.join(settings.TEMP_DIR, "%s.xlsx" % uuid.uuid4().hex)
                result = io.BytesIO()
                workbook = xlsxwriter.Workbook(result)
                worksheet = workbook.add_worksheet(name="Planillado")
                worksheet.set_landscape()
                worksheet.set_paper(9)
                worksheet.center_horizontally()
                worksheet.set_margins(left=0.475, right=0.475, top=0.6, bottom=0.6)
                worksheet.repeat_rows(0, 5)
                worksheet.fit_to_pages(1, 0)
                #
                columnas = [
                    {"titulo": "N°", "campo": "CORR", "centrado": True, "ancho": 2},
                    {"titulo": "DETALLE", "campo": "detalle", "ancho": 8, "centrado": True},
                    {"titulo": "DOCUMENTO", "campo": "destino.documento.nombreDocumentoNumeroMin()", "centrado": True,
                     "ancho": 15},
                    {"titulo": "ORIGEN", "campo": "destino.documento.SiglasDoc()", "centrado": True, "ancho": 10},
                    {"titulo": "DESTINO", "campo": "destino.obtenerNombreDestinoPersona()", "ancho": 30},
                    {"titulo": "DIRECCION", "campo": "direccionYreferencia()", "ancho": 25},
                    {"titulo": "DISTRITO", "campo": "Ubigeo().nombre", "centrado": True, "ancho": 10},
                    {"titulo": "PROVINCIA", "campo": "Ubigeo().provincia.nombre", "centrado": True, "ancho": 10},
                    {"titulo": "DEPART", "campo": "Ubigeo().provincia.departamento.nombre", "centrado": True,
                     "ancho": 10},
                    {"titulo": "PESO", "campo": None, "ancho": 8},
                    {"titulo": "MONTO S/", "campo": None, "ancho": 8},
                    {"titulo": "FECHA DE ENTREGA", "campo": None, "ancho": 8},
                    {"titulo": "FECHA DE NOTIFICACIÓN", "campo": None, "ancho": 10},
                    {"titulo": "FECHA DE DEVOLUCIÓN DE CARGO", "campo": None, "ancho": 10}
                ]
                # Formatos
                format_base = {
                    'bold': True, 'font_size': 14, 'font_name': 'Arial Narrow', "valign": "vcenter", "text_wrap": True
                }
                format_title = workbook.add_format(format_base | {'align': 'center'})
                format_subtitle = workbook.add_format(format_base | {'font_size': 12, 'align': 'center'})
                format_label = workbook.add_format(format_base | {'font_size': 9})
                format_info = workbook.add_format(format_base | {'font_size': 10, 'bold': False})
                format_header = workbook.add_format(format_base | {'align': 'center', 'font_size': 8, "border": True})
                format_cell = workbook.add_format(format_base | {'bold': False, 'font_size': 8, "border": True})
                format_cell_center = workbook.add_format(
                    format_base | {'bold': False, 'align': 'center', 'font_size': 8, "border": True}
                )
                #
                img_escudo = load_bytes(os.path.join(settings.STATICFILES_DIRS[0], 'images', 'escudo_peru.jpg'))
                worksheet.insert_image(
                    'A1', 'img_escudo.jpg',
                    {
                        'x_offset': 5,
                        'y_offset': 10,
                        'x_scale': 1.2,
                        'y_scale': 1.2,
                        'object_position': 2,
                        'image_data': img_escudo,
                    }
                )
                img_logo = load_bytes(os.path.join(settings.STATICFILES_DIRS[0], 'images', 'grc_mini.png'))
                worksheet.insert_image(
                    'M1', 'img_logo.png',
                    {
                        'x_offset': 20,
                        'y_offset': 20,
                        'x_scale': 0.5,
                        'y_scale': 0.5,
                        'object_position': 2,
                        'image_data': img_logo,
                    }
                )
                worksheet.merge_range(0, 0, 0, len(columnas) - 1, "PLANILLADO N° %s - %s" % (
                    cargoexterno.NumeroFull(), cargoexterno.Dependencia()
                ), format_title)
                worksheet.merge_range(1, 0, 1, len(columnas) - 1, formatdate(cargoexterno.fecha), format_subtitle)
                worksheet.write(2, 2, "COURRIER :", format_label)
                worksheet.merge_range(2, 3, 2, len(columnas) - 1, cargoexterno.Nombre(), format_info)
                if cargoexterno.nota:
                    worksheet.write(3, 2, "NOTA :", format_label)
                    worksheet.merge_range(3, 3, 3, len(columnas) - 1, cargoexterno.nota, format_info)
                for idx, columna in enumerate(columnas):
                    worksheet.write(5, idx, columna["titulo"], format_header)
                    worksheet.set_column(idx, idx, columna.get("ancho"))
                for idxf, detalle in enumerate(cargoexterno.destinosOrdenReporte()):
                    for idxc, columna in enumerate(columnas):
                        campo = columna.get("campo")
                        valor = ""
                        if campo == "CORR":
                            valor = idxf + 1
                        elif campo:
                            valor = eval("detalle." + campo) or ""
                        formatocell = format_cell
                        if columna.get("centrado"):
                            formatocell = format_cell_center
                        worksheet.write(6 + idxf, idxc, valor, formatocell)
                #
                # page_footer_font = '&"Arial Narrow,Regular"&8'
                page_footer_font = ''
                page_footer = '&L%s%s&C%s%s%s&R%s%s' % (
                    page_footer_font,
                    settings.CONFIG_APP["TituloCorto"] + " v" + settings.CONFIG_APP["Version"],
                    page_footer_font,
                    "_" * 179 + "\n",
                    "Imp. " + datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p") +
                    " - " + cargoexterno.creador.persona.alias,
                    page_footer_font,
                    "Pág. &P/&N"
                )
                worksheet.set_footer(page_footer)
                workbook.formats[0].font_name = "Arial Narrow"
                workbook.close()
                result.seek(0)
                response = HttpResponse(
                    result,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'inline; filename="Planillado%s.xlsx"' % cargoexterno.NumeroFull()
                return response
            else:
                return HttpResponse("<div>%s</div>" % "No es un formato permitido")
        return super(MensajeriaPlanilladoVista, self).render_to_response(context, **response_kwargs)
