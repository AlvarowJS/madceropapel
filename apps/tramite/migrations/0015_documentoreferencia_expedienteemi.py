# Generated by Django 3.2.9 on 2022-01-04 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0014_auto_20220103_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoreferencia',
            name='expedienteemi',
            field=models.CharField(default='', max_length=100, verbose_name='Número de Emisión'),
        ),
    ]
