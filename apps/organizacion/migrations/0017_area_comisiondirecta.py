# Generated by Django 3.2.9 on 2021-12-10 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0016_area_cargooficial'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='comisiondirecta',
            field=models.BooleanField(default=False),
        ),
    ]
