# Generated by Django 3.2.6 on 2021-11-17 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0006_area_documentoautorizacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='nivel',
            field=models.IntegerField(choices=[(1, 'Primer Nivel'), (2, 'Segundo Nivel'), (3, 'Tercer Nivel')], default=1, verbose_name='Nivel Organizacional'),
        ),
    ]