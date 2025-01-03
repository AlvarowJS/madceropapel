# Generated by Django 3.2.6 on 2021-12-03 21:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0014_auto_20211203_1654'),
        ('tramite', '0005_documentotipo_esmultipledestino'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destino',
            name='dependencia_area',
            field=models.CharField(blank=True, max_length=5, null=True, verbose_name='Unidad Organizacional'),
        ),
        migrations.AlterField(
            model_name='destino',
            name='dependencia_area_nombre',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Unidad Organizacional Nombre'),
        ),
        migrations.AlterField(
            model_name='destino',
            name='tipodestinatario',
            field=models.CharField(choices=[('UO', 'Unidad Organizacional'), ('DP', 'Dependencia'), ('PJ', 'Persona Jurídica'), ('CI', 'Ciudadano')], max_length=2),
        ),
        migrations.AlterField(
            model_name='documento',
            name='areavirtualdestino',
            field=models.CharField(blank=True, max_length=250, null=True, verbose_name='Unidad Organizacional Virtual Destino'),
        ),
        migrations.AlterField(
            model_name='transferencia',
            name='areadestino',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tra_destino', to='organizacion.area', verbose_name='Unidad Organizacional de Destino'),
        ),
        migrations.AlterField(
            model_name='transferencia',
            name='areaorigen',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tra_origen', to='organizacion.area', verbose_name='Unidad Organizacional de Origen'),
        ),
    ]
