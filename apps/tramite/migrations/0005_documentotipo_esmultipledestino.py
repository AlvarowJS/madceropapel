# Generated by Django 3.2.6 on 2021-12-02 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0004_documentotipo_autorizacomision'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentotipo',
            name='esmultipledestino',
            field=models.BooleanField(default=False, verbose_name='Es Múltiple Destino'),
        ),
    ]
