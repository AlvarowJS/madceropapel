"""
@autor Dirección Regional de Transformación Digital
@titularidad GOBIERNO REGIONAL CAJAMARCA
@licencia Python Software Foundation License. Ver LICENCIA.txt
@año 2022
"""

from django.urls import path

from apps.inicio.vistas.dashboard import DashboardDatos, Dashboard
from apps.inicio.vistas.inicio import Inicio, InicioBlank
from apps.inicio.vistas.login import InicioLogin, InicioLogout, InicioChangePassword, InicioInfo, AreaChange, \
    AreaChangeListar, InicioResetPassword, InicioResetPasswordDone, InicioResetPasswordPrevio, \
    InicioResetPasswordConfirm, InicioResetPasswordConfirmOk
from apps.inicio.vistas.persona import PersonaListar, AdmPersona, AdmPersonaListar, AdmPersonaAgregar, AdmPersonaEditar
from apps.inicio.vistas.personajuridica import PersonaJuridicaListar, PersonaJuridicaRzListar
from apps.inicio.vistas.pj import PJVista, PJListar, PJAgregar, PJEditar, PJEliminar
from apps.inicio.vistas.scanqr import ScanQRVista, ScanQRVista
from apps.inicio.vistas.tipodocumentoidentidad import TipoDocumentoIdentidadListar

app_name = "appini"

urlpatterns = [
    path('', Inicio.as_view(), name="inicio"),
    path('blank', InicioBlank.as_view(), name="inicio_blank"),
    path('login', InicioLogin.as_view(), name="inicio_login"),
    path('logout', InicioLogout.as_view(), name="inicio_logout"),
    path('changepassword', InicioChangePassword.as_view(), name="inicio_cambiar_password"),
    path('resetpassword', InicioResetPassword.as_view(), name="inicio_reset_password"),
    path('resetpassword/done', InicioResetPasswordDone.as_view(), name="inicio_reset_password_done"),
    path('resetpassword/confirm/<str:uidb64>/<str:token>', InicioResetPasswordConfirm.as_view(),
         name="inicio_reset_password_confirm"),
    path('resetpassword/confirm/ok', InicioResetPasswordConfirmOk.as_view(),
         name="inicio_reset_password_confirm_ok"),
    path('resetpassword/previo', InicioResetPasswordPrevio.as_view(), name="inicio_reset_password_previo"),
    path('info', InicioInfo.as_view(), name="inicio_info"),
    path('changearea', AreaChange.as_view(), name="area_change"),
    path('changearea/listar', AreaChangeListar.as_view(), name="area_change_listar"),

    # Scan QR
    path('scanqr', ScanQRVista.as_view(), name="scan_qr"),

    # Combos
    path('personajuridica/listar', PersonaJuridicaListar.as_view(), name="personajuridica_listar"),
    path('personajuridicarz/listar', PersonaJuridicaRzListar.as_view(), name="personajuridicarz_listar"),
    path('persona/listar', PersonaListar.as_view(), name="persona_listar"),

    path('admpersona', AdmPersona.as_view(), name="adm_persona"),
    path('admpersona/listar', AdmPersonaListar.as_view(), name="adm_persona_listar"),
    path('admpersona/agregar', AdmPersonaAgregar.as_view(), name="adm_persona_agregar"),
    path('admpersona/editar/<int:pk>', AdmPersonaEditar.as_view(), name="adm_persona_editar"),

    path('tipodocumentoidentidad/listar', TipoDocumentoIdentidadListar.as_view(), name="tipodocumentoidentidad_listar"),

    path('dashboard', Dashboard.as_view(), name="dashboard"),
    path('dashboard/<str:codigo>', DashboardDatos.as_view(), name="dashboard_datos"),

    # Administración de Personas Jurídicas
    path('pj', PJVista.as_view(), name="pj_vista"),
    path('pj/listar/<str:modo>', PJListar.as_view(), name="pj_listar"),
    path('pj/agregar/<str:modo>', PJAgregar.as_view(), name="pj_agregar"),
    path('pj/editar/<int:pk>', PJEditar.as_view(), name="pj_editar"),
    path('pj/eliminar/<int:pk>', PJEliminar.as_view(), name="pj_eliminar"),

]
