# Generated by Django 3.2.9 on 2022-01-03 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0013_documentopdfrevisiones'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='confidencialenviado',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Reservado Enviado'),
        ),
        migrations.AlterField(
            model_name='documento',
            name='confidencial',
            field=models.BooleanField(default=False, verbose_name='Reservado/Confidencial'),
        ),
        migrations.AlterField(
            model_name='documento',
            name='confidencialclave',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Reservado Clave'),
        ),
        migrations.AlterField(
            model_name='documento',
            name='confidencialencriptado',
            field=models.BooleanField(default=False, verbose_name='Reservado Encriptado'),
        ),
    ]