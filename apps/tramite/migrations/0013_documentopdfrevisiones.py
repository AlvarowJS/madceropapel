# Generated by Django 3.2.9 on 2021-12-30 16:21

import dirtyfields.dirtyfields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tramite', '0012_alter_documento_ciudadanocargo'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentoPDFRevisiones',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True, null=True)),
                ('direccionip', models.GenericIPAddressField(blank=True, null=True, verbose_name='Dirección IP')),
                ('nombreequipo', models.CharField(blank=True, max_length=200, null=True, verbose_name='Nombre de Equipo')),
                ('es_mobile', models.BooleanField(default=False, verbose_name='Es Mobile')),
                ('es_tablet', models.BooleanField(default=False, verbose_name='Es Tablet')),
                ('es_touch', models.BooleanField(default=False, verbose_name='Es Touch')),
                ('es_pc', models.BooleanField(default=False, verbose_name='Es PC')),
                ('es_bot', models.BooleanField(default=False, verbose_name='Es BOT')),
                ('navegador_familia', models.CharField(blank=True, max_length=200, null=True, verbose_name='Navegador Familia')),
                ('navegador_version', models.CharField(blank=True, max_length=200, null=True, verbose_name='Navegador Versión')),
                ('so_familia', models.CharField(blank=True, max_length=200, null=True, verbose_name='S.O. Familia')),
                ('so_version', models.CharField(blank=True, max_length=200, null=True, verbose_name='S.O. Versión')),
                ('device_familia', models.CharField(blank=True, max_length=200, null=True, verbose_name='Device Familia')),
                ('creador', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('documentopdf', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='revisiones', to='tramite.documentopdf', verbose_name='Documento PDF')),
                ('editor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Revisión',
                'verbose_name_plural': 'Revisiones',
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]
