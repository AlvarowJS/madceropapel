# Generated by Django 4.0.5 on 2022-06-27 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0062_documentotipo_paraderivacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='anularemision',
            field=models.BooleanField(default=False, verbose_name='Permitir Anular Emisión'),
        ),
    ]
