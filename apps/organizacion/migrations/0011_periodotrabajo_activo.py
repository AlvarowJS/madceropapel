# Generated by Django 3.2.6 on 2021-11-23 17:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0010_remove_area_documentosustento'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodotrabajo',
            name='activo',
            field=models.BooleanField(default=True),
        ),
    ]