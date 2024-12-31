"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from datetime import datetime

import django.forms.models
from django import forms

# ===================================== INPUT
from django.conf import settings
from django.db.models import ImageField as ImgField, TextField as TxtField
from django.forms import Widget, CheckboxInput
from django.forms.widgets import ChoiceWidget


class Input(Widget):
    input_type = None  # Subclasses must define this.
    template_name = 'clases/campos/input.html'

    def __init__(self, attrs=None):
        if attrs is not None:
            attrs = attrs.copy()
            self.input_type = attrs.pop('type', self.input_type)
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['type'] = self.input_type
        return context


# ===================================== INPUT TEXT

class AppInputTextWidget(Input):
    input_type = 'text'
    template_name = "clases/campos/text.html"

    def __init__(self, placeholder=None, placeholderlabel=None, password=False, conlabel=None, iconappend=None,
                 iconprepend=None, buttonappend=None, mask=None, minlength=None, maxlength=None, input_type='text',
                 textappend=None, label=None, flotante=False):
        super(AppInputTextWidget, self).__init__()
        self.flotante = flotante
        self.label = label
        self.conlabel = conlabel
        self.iconappend = iconappend
        self.textappend = textappend
        self.iconprepend = iconprepend
        self.buttonappend = buttonappend
        self.placeholder = placeholder
        self.placeholderlabel = placeholderlabel
        self.password = password
        self.mask = mask
        self.minlength = minlength
        self.maxlength = maxlength
        self.input_type = input_type

    def get_context(self, name, value, attrs):
        context = super(AppInputTextWidget, self).get_context(name, value, attrs)
        if not context["widget"]["attrs"].get("class", "").__contains__("form-control"):
            context["widget"]["attrs"]["class"] = (
                    context["widget"]["attrs"].get("class", "") + " form-control"
            ).strip()
        context["widget"]["flotante"] = self.flotante
        if self.flotante:
            context["widget"]["attrs"]["placeholder"] = ""
        context["widget"]["label"] = self.label
        context["widget"]["conlabel"] = self.conlabel
        if self.iconappend or self.textappend:
            context["widget"]["iconappend"] = self.iconappend
            context["widget"]["textappend"] = self.textappend
            context["widget"]["attrs"]["class"] += " no-border-bottom-right-radius no-border-top-right-radius"
        context["widget"]["iconprepend"] = self.iconprepend
        context["widget"]["buttonappend"] = self.buttonappend
        if self.minlength:
            context["widget"]["attrs"]["minlength"] = self.minlength
        if self.maxlength:
            context["widget"]["attrs"]["maxlength"] = self.maxlength
        if self.password:
            context["widget"]["type"] = "password"
            context["widget"]["attrs"]["autocomplete"] = "current-password"
        if self.placeholder:
            context["widget"]["attrs"]["placeholder"] = self.placeholder
        if self.placeholderlabel:
            context["widget"]["placeholderlabel"] = self.placeholderlabel
        if self.mask:
            context["widget"]["attrs"]["data-mask"] = ""
            context["widget"]["attrs"]["data-inputmask"] = "'mask': '%s'" % self.mask
            context["widget"]["attrs"]["maxlength"] = len(self.mask)
        return context


class AppInputText(forms.CharField):

    def __init__(self, placeholder=None, password=False, conlabel=True,
                 iconappend=None, iconprepend=None, flotante=False, *args, **kwargs):
        super(AppInputText, self).__init__(*args, **kwargs)
        self.widget = AppInputTextWidget(
            password=password, placeholder=placeholder, conlabel=conlabel,
            iconappend=iconappend, iconprepend=iconprepend, minlength=self.min_length,
            maxlength=self.max_length, flotante=flotante, label=self.label
        )


# ===================================== INPUT NUMBER
class AppInputNumberWidget(Input):
    input_type = 'number'
    template_name = "clases/campos/number.html"

    def __init__(self, placeholder=None, minimo=None, maximo=None, css=None):
        super(AppInputNumberWidget, self).__init__()
        self.placeholder = placeholder
        self.minimo = minimo
        self.maximo = maximo
        self.css = css

    def get_context(self, name, value, attrs):
        context = super(AppInputNumberWidget, self).get_context(name, value, attrs)
        css = " " + (self.css or "")
        if not context["widget"]["attrs"].get("class", "").__contains__("form-control"):
            context["widget"]["attrs"]["class"] = (
                    context["widget"]["attrs"].get("class", "") + " form-control"
            ).strip()
        context["widget"]["attrs"]["class"] = context["widget"]["attrs"].get("class", "") + css
        if self.placeholder:
            context["widget"]["attrs"]["placeholder"] = self.placeholder
        context["widget"]["attrs"]["data-min"] = "null" if self.minimo is None else self.minimo
        context["widget"]["attrs"]["data-max"] = "null" if self.maximo is None else self.maximo
        context["widget"]["attrs"]["data-verticalbuttons"] = "true"
        context["widget"]["attrs"]["data-verticalup"] = "<i class='fa fa-plus text-xs text-white'></i>"
        context["widget"]["attrs"]["data-verticaldown"] = "<i class='fa fa-minus text-xs text-white'></i>"
        context["widget"]["attrs"]["data-verticalupclass"] = "btn-sm"
        context["widget"]["attrs"]["data-verticaldownclass"] = "btn-sm"
        return context


class AppInputNumber(forms.IntegerField):

    def __init__(self, placeholder=None, minimo=None, maximo=None, css=None, *args, **kwargs):
        super(AppInputNumber, self).__init__(*args, **kwargs)
        self.widget = AppInputNumberWidget(placeholder=placeholder, minimo=minimo, maximo=maximo, css=css)


# ===================================== TEXT AREA
class TextAreaWidget(forms.Textarea):
    input_type = None
    template_name = 'clases/campos/textarea.html'

    def __init__(self, placeholder=None, placeholderlabel=None, *args, **kwargs):
        super(TextAreaWidget, self).__init__(*args, **kwargs)
        self.placeholder = placeholder
        self.placeholderlabel = placeholderlabel

    def get_context(self, name, value, attrs):
        context = super(TextAreaWidget, self).get_context(name, value, attrs)
        if not context["widget"]["attrs"].get("class", "").__contains__("form-control"):
            context["widget"]["attrs"]["class"] = (
                    context["widget"]["attrs"].get("class", "") + " form-control"
            ).strip()
        if self.placeholder:
            context["widget"]["attrs"]["placeholder"] = self.placeholder
        if self.placeholderlabel:
            context["widget"]["placeholderlabel"] = self.placeholderlabel
        return context


class TextAreaAutoWidget(forms.Textarea):
    input_type = None
    template_name = 'clases/campos/textarea.html'

    def __init__(self, placeholder=None, placeholderlabel=None, *args, **kwargs):
        super(TextAreaAutoWidget, self).__init__(*args, **kwargs)
        self.placeholder = placeholder
        self.placeholderlabel = placeholderlabel

    def get_context(self, name, value, attrs):
        context = super(TextAreaAutoWidget, self).get_context(name, value, attrs)
        if not context["widget"]["attrs"].get("class", "").__contains__("form-control"):
            context["widget"]["attrs"]["class"] = (
                    context["widget"]["attrs"].get("class", "") + " form-control max-h-150px overflow-auto"
            ).strip()
        if self.placeholder:
            context["widget"]["attrs"]["placeholder"] = self.placeholder
        if self.placeholderlabel:
            context["widget"]["placeholderlabel"] = self.placeholderlabel
        context["widget"]["attrs"]["rows"] = 1
        return context


# ===================================== RADIO SELECT
class RadioSelectWidget(ChoiceWidget):
    input_type = 'radio'
    template_name = 'clases/campos/radio.html'
    option_template_name = 'clases/campos/radio_option.html'

    def __init__(self, orientation="vertical", attrsfields=None, clase=None, *args, **kwargs):
        super(RadioSelectWidget, self).__init__(*args, **kwargs)
        self.clase = clase
        self.attrs = {"class": "custom-control-input " + self.attrs.get("class", "")}
        self.orientation = orientation
        self.attrsfields = attrsfields

    def get_context(self, name, value, attrs):
        context = super(RadioSelectWidget, self).get_context(name, value, attrs)
        context["widget"]["attrs"]["data-live-search"] = "true"
        context["widget"]["clase"] = self.clase
        return context

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super(RadioSelectWidget, self).create_option(name, value, label, selected, index, subindex, attrs)
        if self.attrsfields:
            objeto = self.choices.__dict__["queryset"][index]
            for atributo in self.attrsfields:
                valor = eval("objeto." + atributo)
                if isinstance(valor, bool):
                    valor = int(valor)
                elif not isinstance(valor, str):
                    valor = repr(valor)
                option['attrs']["data-" + atributo] = valor
        option['attrs']["data-text"] = option['label']
        return option


# ===================================== CHECK MULTI
class MultiCheckWidget(ChoiceWidget):
    allow_multiple_selected = True
    input_type = 'checkbox'
    template_name = 'clases/campos/checkbox_multi.html'
    option_template_name = 'clases/campos/checkbox_option.html'

    def __init__(self, orientation="vertical", columnas=2, *args, **kwargs):
        super(MultiCheckWidget, self).__init__(*args, **kwargs)
        self.attrs = {"class": "custom-control-input"}
        self.orientation = orientation
        self.columnas = columnas

    def get_context(self, name, value, attrs):
        context = super(MultiCheckWidget, self).get_context(name, value, attrs)
        context["widget"]["columnas"] = self.columnas
        for opt in context["widget"]["optgroups"]:
            del opt[1][0]["attrs"]["required"]
        return context


# ===================================== CHECK
class CheckWidget(CheckboxInput):
    template_name = 'clases/campos/checkbox.html'

    def __init__(self, oncolor="success", offcolor="warning", ontext=None, offtext=None, *args, **kwargs):
        super(CheckWidget, self).__init__(*args, **kwargs)
        self.__oncolor = oncolor
        self.__offcolor = offcolor
        self.__ontext = ontext
        self.__offtext = offtext
        self.label_class = "d-block"

    def get_context(self, name, value, attrs):
        context = super(CheckWidget, self).get_context(name, value, attrs)
        # context["widget"]["attrs"]["class"] += " d-block"
        context["widget"]["attrs"]["data-switch"] = "true"
        context["widget"]["attrs"]["data-on-color"] = self.__oncolor
        context["widget"]["attrs"]["data-off-color"] = self.__offcolor
        context["widget"]["attrs"]["data-size"] = "normal"
        if self.__ontext:
            context["widget"]["attrs"]["data-on-text"] = self.__ontext
        if self.__offtext:
            context["widget"]["attrs"]["data-off-text"] = self.__offtext
        return context


# ===================================== ICON SELECT
class WidgetIcono(forms.TextInput):
    input_type = 'text'
    template_name = 'clases/campos/icon_select.html'


class ModelWidgetIcono(forms.CharField):

    def __init__(self, **kwargs):
        super(ModelWidgetIcono, self).__init__(**kwargs)
        self.widget = WidgetIcono()


# ===================================== COLOR SELECT
class WidgetColor(forms.TextInput):
    def get_context(self, name, value, attrs):
        context = super(WidgetColor, self).get_context(name, value, attrs)
        context["widget"]["attrs"]["class"] += " color-selector"
        return context


class ModelWidgetColor(forms.CharField):
    def __init__(self, **kwargs):
        super(ModelWidgetColor, self).__init__(**kwargs)
        self.widget = WidgetColor()


# ===================================== DATE AND DATETIME
class FechaInput(forms.DateInput):
    format_key = 'DATE_INPUT_FORMATS'
    template_name = 'clases/campos/date.html'


class HoraInput(forms.TimeInput):
    template_name = 'clases/campos/time.html'


class FechaHoraInput(forms.DateInput):
    format_key = 'DATE_INPUT_FORMATS'
    template_name = 'clases/campos/datetime.html'


class WidgetFecha(FechaInput):
    def __init__(self, type, format, input_formats, placeholderlabel=None, mindate=None, *args, **kwargs):
        super(WidgetFecha, self).__init__(*args, **kwargs)
        self.format = format
        self.input_formats = input_formats
        self.placeholderlabel = placeholderlabel
        self.type = type
        self.attrs[type + "-picker"] = ""
        self.attrs["readonly"] = ""
        if mindate:
            self.attrs["data-startdate"] = mindate.strftime("%Y-%m-%d")

    def get_context(self, name, value, attrs):
        context = super(WidgetFecha, self).get_context(name, value, attrs)
        if self.format:
            if value:
                if isinstance(value, str):
                    value = datetime.strptime(value, self.input_formats[0])
                value = value.strftime(self.input_formats[0])
        context['widget']['value'] = value
        context['widget']['format'] = self.format
        context['widget']['placeholderlabel'] = self.placeholderlabel
        if self.type == "datetime":
            context["widget"]["attrs"]["class"] += " datetimepicker-input"
            context["widget"]["attrs"]["data-target"] = "#%s_ctrl" % context["widget"]["attrs"]["id"]
        return context


class WidgetHora(HoraInput):
    def __init__(self, placeholderlabel=None, *args, **kwargs):
        super(WidgetHora, self).__init__(*args, **kwargs)
        self.format = "%I:%M %p"
        self.input_formats = ["%I:%M %p"]
        self.placeholderlabel = placeholderlabel
        self.attrs["time-picker"] = ""
        self.attrs["readonly"] = ""

    def get_context(self, name, value, attrs):
        context = super(WidgetHora, self).get_context(name, value, attrs)
        if self.format:
            if value:
                if isinstance(value, str):
                    value = datetime.strptime(value, self.input_formats[0])
                value = value.strftime(self.input_formats[0])
        context["widget"]["attrs"]["class"] = "form-control"
        context['widget']['value'] = value
        context['widget']['format'] = self.format
        context['widget']['placeholderlabel'] = self.placeholderlabel
        return context


class ModelWidgetMonthYear(forms.DateField):
    def __init__(self, **kwargs):
        super(ModelWidgetMonthYear, self).__init__(**kwargs)
        self.input_formats = ["%m/%Y"]
        self.widget = WidgetFecha(type="period", format="mm/yyyy", input_formats=self.input_formats)


# ===================================== CROP IMAGEN
class WidgetImageCrop(forms.ClearableFileInput):
    template_name = 'clases/campos/image_file_input.html'


class ModelWidgetImageCrop(forms.ImageField):
    widget = WidgetImageCrop

    def __init__(self, width=None, height=None, width_mini=None, height_mini=None, *args, **kwargs):
        self.width = width
        self.width_mini = width_mini
        self.height = height
        self.height_mini = height_mini
        super(ModelWidgetImageCrop, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        wg = super(ModelWidgetImageCrop, self).widget_attrs(widget=widget)
        wg.update({
            "data-crop-image": ""
        })
        if self.width:
            wg.update({"data-width": self.width})
        if self.height:
            wg.update({"data-height": self.height})
        if self.width_mini:
            wg.update({"data-widthmini": self.width_mini})
        if self.height_mini:
            wg.update({"data-heightmini": self.height_mini})
        return wg


class ModelImageField(ImgField):

    def __init__(self, width=None, height=None, width_mini=None, height_mini=None, field_mini=None, *args, **kwargs):
        super(ModelImageField, self).__init__(*args, **kwargs)
        self.width, self.height, self.width_mini, self.height_mini, self.field_mini = \
            width, height, width_mini, height_mini, field_mini

    def formfield(self, **kwargs):
        kwargs.update({
            "width": self.width,
            "height": self.height,
            "width_mini": self.width_mini,
            "height_mini": self.height_mini,
        })
        return super().formfield(**{
            'form_class': ModelWidgetImageCrop,
            **kwargs,
        })


class ModelWidgetImage2(forms.ImageField):

    def __init__(self, width=None, height=None, width_mini=None, height_mini=None, *args, **kwargs):
        self.width = width
        self.height = height
        super(ModelWidgetImage2, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        wg = super(ModelWidgetImage2, self).widget_attrs(widget=widget)
        wg.update({"data-crop-image": ""})
        if self.width:
            wg.update({"data-width": self.width})
        if self.height:
            wg.update({"data-height": self.height})
        return wg


class ImageField2(ImgField):
    def __init__(self, width=None, height=None, *args, **kwargs):
        super(ImageField2, self).__init__(*args, **kwargs)
        self.width, self.height = width, height

    def formfield(self, **kwargs):
        kwargs.update({
            "width": self.width,
            "height": self.height
        })
        return super().formfield(**{
            'form_class': ModelWidgetImage2,
            **kwargs,
        })


# ===================================== PUNTO GEO
class WidgetPuntoGeo(Widget):
    input_type = None
    template_name = 'clases/campos/puntogeo.html'

    def get_context(self, name, value, attrs):
        if value:
            values = value.splitlines()
            attrs.update({
                "data-lat": values[0],
                "data-lng": values[1],
                "data-zoom": values[2],
                "data-dir": values[3]
            })
        else:
            attrs.update({
                "data-lat": "0",
                "data-lng": "0",
                "data-zoom": "16",
                "data-dir": ""
            })
        context = super(WidgetPuntoGeo, self).get_context(name, value, attrs)
        context["widget"]["copy_url"] = settings.CONFIG_APP["AppSite"]
        context["widget"]["copy_name"] = settings.CONFIG_APP["Titulo"]
        context["widget"]["copy_key"] = settings.CONFIG_APP["KeyMap_leaflet"]
        return context


class ModelWidgetPuntoGeo(forms.Textarea):
    widget = WidgetPuntoGeo


class ModelPuntoGeo(TxtField):
    def formfield(self, **kwargs):
        return super().formfield(**{
            'max_length': self.max_length,
            **({'widget': WidgetPuntoGeo}),
            **kwargs,
        })


# ===================================== EDITOR HTML
class WidgetEditorField(forms.Textarea):
    input_type = None
    template_name = 'clases/campos/editor.html'

    def __init__(self, *args, **kwargs):
        super(WidgetEditorField, self).__init__(*args, **kwargs)


class ModelEditorField(forms.CharField):
    widget = WidgetEditorField

    def __init__(self, alto=100, placeholder=None, *args, **kwargs):
        self.alto = alto
        self.placeholder = placeholder
        super(ModelEditorField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.alto:
            attrs['alto'] = str(self.alto)
        if self.placeholder:
            attrs['placeholder'] = str(self.placeholder)
        return attrs


# ===================================== INPUT FILE
class ModelFileInput(forms.FileInput):
    template_name = "clases/campos/file.html"

    def __init__(self, extensiones=None, maxsize=None, clase=None, folder=False, *args, **kwargs):
        super(ModelFileInput, self).__init__(*args, **kwargs)
        self.clase = clase
        self.extensiones = extensiones
        self.maxsize = maxsize
        self.folder = folder

    def get_context(self, name, value, attrs):
        context = super(ModelFileInput, self).get_context(name, value, attrs)
        context["widget"]["attrs"]["class"] += (self.clase or "")
        context["widget"]["extensiones"] = self.extensiones or "null"
        if self.folder:
            context["widget"]["folder"] = self.folder
            context["widget"]["attrs"]["multiple"] = "multiple"
            context["widget"]["attrs"]["webkitdirectory"] = "webkitdirectory"
        #
        if self.extensiones:
            context["widget"]["attrs"]["accept"] = ",".join(["." + extension for extension in self.extensiones])
        #
        context["widget"]["maxsize"] = self.maxsize or 0
        return context


class ModelFileField(forms.FileField):

    def __init__(self, extensiones=None, maxsize=None, clase=None, folder=False, *args, **kwargs):
        super(ModelFileField, self).__init__(*args, **kwargs)
        self.clase = clase
        self.extensiones = extensiones
        self.maxsize = maxsize
        self.widget = ModelFileInput(clase=clase, extensiones=extensiones, maxsize=maxsize, folder=folder)
