# Generated by Django 4.0.3 on 2022-03-16 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0035_auto_20220306_2113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cargoexternoestado',
            name='estado',
            field=models.CharField(choices=[('GN', 'Generado'), ('CE', 'Cerrado'), ('FI', 'Finalizado')], max_length=2),
        ),
        migrations.AlterField(
            model_name='documento',
            name='origentipo',
            field=models.CharField(choices=[('O', 'EMISIÓN DE OFICINA'), ('P', 'EMISIÓN PROFESIONAL'), ('F', 'MESA DE PARTES FÍSICA'), ('V', 'MESA DE PARTES VIRTUAL'), ('X', 'INTEROPERABILIDAD'), ('C', 'COURRIER'), ('A', 'ACCESO A LA INFORMACIÓN')], max_length=1),
        ),
    ]