"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

import json
import random

from PIL import Image
import os
from io import BytesIO

from dirtyfields import DirtyFieldsMixin
from django.core.files.base import ContentFile

import django
from babel.dates import format_date, format_datetime
from django.contrib.auth.models import User
from django.db import models
from django.forms import model_to_dict
from django.utils.translation import gettext_lazy as _

from django import forms

import modulos
from modulos.utiles.clases.campos import RadioSelectWidget, CheckWidget, WidgetColor, WidgetFecha, ModelWidgetImageCrop, \
    AppInputNumberWidget, TextAreaWidget, TextAreaAutoWidget
from modulos.utiles.clases.varios import randomString


class AuditoriaManager(models.Manager):
    def get_queryset(self):
        return super(AuditoriaManager, self).get_queryset()


class Auditoria(DirtyFieldsMixin, models.Model):
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True, null=True)
    creador = models.ForeignKey(User, related_name='+', on_delete=models.PROTECT)
    editor = models.ForeignKey(User, related_name='+', blank=True, null=True, on_delete=models.PROTECT)
    # edicioncode = models.CharField(max_length=5, default=randomString())
    uppers = []

    objects = AuditoriaManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.__unicode__()

    @staticmethod
    def get_absolute_url():
        return ""

    def Creado(self):
        _result = ""
        if self.creado:
            _result = format_date(self.creado, "dd 'de' MMMM 'de' Y", locale="es")
        return _result

    def CreadoHora(self):
        _result = ""
        if self.creado:
            _result = format_datetime(self.creado, "dd 'de' MMMM 'de' Y hh:mm a", locale="es")
        return _result

    def Creador(self):
        _result = ""
        if self.creador:
            _result = "%s" % self.creador.userprofile.persona.alias
        return _result

    def __init__(self, *args, **kwargs):
        super(Auditoria, self).__init__(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        for field in self._meta.fields:
            if field.__class__ in [django.db.models.fields.files.ImageField,
                                   django.db.models.fields.files.FileField,
                                   modulos.utiles.clases.campos.ModelImageField]:
                if self.id:
                    this = self._meta.model.objects.get(id=self.id)
                    if this:
                        if eval("this." + field.name) != eval("self." + field.name):
                            eval("this." + field.name).delete(save=False)
                            if hasattr(field, "field_mini"):
                                if field.field_mini:
                                    eval("this." + field.field_mini).delete(save=False)
                if eval("self." + field.name) and hasattr(field, "field_mini"):
                    if field.field_mini and field.width_mini and field.height_mini:
                        fieldImg = eval("self." + field.name)
                        image = Image.open(fieldImg)
                        image.thumbnail([field.width_mini, field.height_mini], Image.ANTIALIAS)
                        thumb_basename = os.path.basename(fieldImg.name)
                        thumb_name, thumb_extension = os.path.splitext(thumb_basename)
                        thumb_extension = thumb_extension.lower()
                        thumb_filename = thumb_name + '_thumb' + thumb_extension
                        thumb_type = thumb_extension[1:].upper()
                        if thumb_type in ['JPG']:
                            thumb_type = 'JPEG'
                        temp_thumb = BytesIO()
                        image.save(temp_thumb, thumb_type)
                        temp_thumb.seek(0)
                        eval("self." + field.field_mini).save(
                            thumb_filename, ContentFile(temp_thumb.read()), save=False
                        )
                        temp_thumb.close()
        for textUP in self.uppers:
            exec("self.%s = str(self.%s).upper()" % (textUP, textUP))
        # if not self.edicioncode:
        #     self.edicioncode = randomString()
        super(Auditoria, self).save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        for field in self._meta.fields:
            if field.__class__ in [
                django.db.models.fields.files.ImageField,
                django.db.models.fields.files.FileField,
                modulos.utiles.clases.campos.ModelImageField
            ]:
                eval("self." + field.name).delete(save=False)
        super(Auditoria, self).delete(using, keep_parents)


class UpperCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        self.is_uppercase = kwargs.pop('uppercase', False)
        super(UpperCharField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super(UpperCharField, self).get_prep_value(value)
        if self.is_uppercase:
            return value.upper()
        return value


EstadosSiNo = ((True, "Si"), (False, "No"))

EstadosActIna = ((True, "Activo"), (False, "Inactivo"))

ListaMeses = (
    (1, str(_("January"))),
    (2, str(_("Febrary"))),
    (3, str(_("March"))),
    (4, str(_("April"))),
    (5, str(_("May"))),
    (6, str(_("June"))),
    (7, str(_("July"))),
    (8, str(_("August"))),
    (9, str(_("September"))),
    (10, str(_("October"))),
    (11, str(_("November"))),
    (12, str(_("December")))
)

ListaDias = (
    (1, str(_("Lunes"))),
    (2, str(_("Martes"))),
    (3, str(_("Miercoles"))),
    (4, str(_("Jueves"))),
    (5, str(_("Viernes"))),
    (6, str(_("Sabado"))),
    (7, str(_("Domingo"))),
)


class AppBaseForm(object, ):
    firstfield = None
    fieldstipodoc = None

    def __init__(self, *args, **kwargs):
        self.id = "form%s" % random.randint(1000, 100000)
        if "kwargs" in kwargs:
            self.kwargs = kwargs.pop("kwargs")
        if "request" in kwargs:
            self.request = kwargs.pop("request")
        super(AppBaseForm, self).__init__(*args, **kwargs)
        campofocus = None
        campoform = None
        for key, field in self.fields.items():
            clase = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = ' '.join([clase, 'form-control']).strip()
            if key == self.firstfield:
                campofocus = key
            try:
                campoform = self._meta.model._meta.get_field(key)
                campolabel = campoform.verbose_name
                if not field.label or field.label == key:
                    if str(campolabel).islower():
                        campolabel = str(campolabel).capitalize()
                    field.label = campolabel
            except:
                pass
            if field.widget.__class__ == WidgetColor:
                field.widget.attrs["class"] += " color-selector"
            elif field.widget.__class__ == django.forms.widgets.NumberInput:
                field.widget = AppInputNumberWidget(minimo=0)
                if field.__class__ in [django.forms.fields.IntegerField]:
                    field.widget.attrs["data-decimals"] = "0"
                    field.widget.attrs["data-step"] = "1"
                else:
                    field.widget.attrs["data-decimals"] = "2"
                    field.widget.attrs["data-step"] = "0.01"
                field.widget.attrs["class"] = "form-control text-center mr-4"
                field.widget.attrs["data-verticalbuttons"] = "true"
                field.widget.attrs["data-verticalup"] = "<i class='fa fa-plus text-xs text-white'></i>"
                field.widget.attrs["data-verticaldown"] = "<i class='fa fa-minus text-xs text-white'></i>"
                field.widget.attrs["data-verticalupclass"] = "btn-sm"
                field.widget.attrs["data-verticaldownclass"] = "btn-sm"
            elif field.widget.__class__ == django.forms.widgets.Textarea:
                field.widget = TextAreaWidget()
                field.widget.attrs["rows"] = "3"
                field.widget.attrs["style"] = "resize: none"
                if hasattr(campoform, "max_length"):
                    field.widget.attrs["maxlength"] = campoform.max_length
            elif field.widget.__class__ == TextAreaAutoWidget:
                if campoform.max_length:
                    field.widget.attrs["maxlength"] = campoform.max_length
            elif field.widget.__class__ == django.forms.RadioSelect:
                field.widget.attrs["class"] += " custom-control-input"
                field.widget = RadioSelectWidget(attrs=field.widget.attrs, choices=field.widget.choices)
            elif field.widget.__class__ == django.forms.widgets.CheckboxInput or \
                    field.__class__ == django.forms.fields.TypedChoiceField:
                hecho = False
                if campoform:
                    if campoform.__class__ == django.db.models.fields.BooleanField:
                        hecho = True
                if not hecho and hasattr(field, "choices"):
                    if field.widget.__class__ in [RadioSelectWidget]:
                        field.widget.attrs["class"] = "custom-control-input"
                    else:
                        field.widget.attrs["data-style"] = "btn btn-outline-primary"
                        field.widget.attrs["class"] += " selectpicker"
                        if len(field.choices) > 4:
                            field.widget.attrs["data-live-search"] = "true"
                else:
                    field.required = False
                    field.widget = CheckWidget(field.widget.attrs)
                    field.widget.attrs["class"] = "switch-input"
            elif field.widget.__class__ == django.forms.widgets.Select or field.widget.input_type == "select":
                if field.widget.__class__ in [django.forms.widgets.Select]:
                    field.widget.attrs["class"] += " selectpicker"
                    field.widget.attrs["data-minimum-results-for-search"] = "-1"
                    if len(field.choices) > 4:
                        field.widget.attrs["data-live-search"] = "true"
                    field.empty_label = None
                else:
                    field.widget.attrs["data-allow-clear"] = str(not field.required).lower()
                field.widget.attrs["style"] = "width: 100%"
                field.widget.attrs["data-minimum-input-length"] = "0"
            elif field.widget.__class__ == django.forms.widgets.DateInput:
                field.input_formats = ["%d/%m/%Y"]
                attrs = field.widget.attrs
                attrs.update({"placeholder": field.label})
                field.widget = WidgetFecha(
                    type="date", format="DD/MM/YYYY", input_formats=field.input_formats,
                    attrs=attrs, placeholderlabel=True
                )
            elif field.widget.__class__ == django.forms.widgets.DateTimeInput:
                field.input_formats = ["%d/%m/%Y %I:%M %p"]
                attrs = field.widget.attrs
                attrs.update({"placeholder": field.label})
                field.widget = WidgetFecha(
                    type="datetime", format="DD/MM/YYYY h:mm A", input_formats=field.input_formats,
                    attrs=attrs, placeholderlabel=True
                )
            elif field.widget.__class__ == django.forms.widgets.TimeInput:
                field.widget.attrs["timepicker"] = ""
                field.input_formats = ["%I:%M %p"]
            elif field.__class__ in [
                django.forms.fields.ImageField,
                django.forms.fields.FileField
            ]:
                field.widget.attrs["class"] += " custom-file-input"
                field.widget.attrs["file-upload"] = ""
                if self.instance.pk:
                    field.required = False
        if self.fieldstipodoc:
            selector = self.fieldstipodoc.get("selector")
            numero = self.fieldstipodoc.get("numero")
            if selector and numero:
                self.fields[selector].widget.attrs["data-numero"] = numero
                self.fields[numero].widget.attrs["data-selector"] = selector
                self.fields[selector].widget.attrs["data-selector-comp"] = json.dumps(list(
                    self.fields[selector].queryset.values(
                        "id", "longitud", "exacto", "tipo"
                    )
                ))
        if campofocus:
            self.fields[campofocus].widget.attrs['autofocus'] = 'autofocus'


class AppBaseModelForm(AppBaseForm, forms.ModelForm):
    pass
