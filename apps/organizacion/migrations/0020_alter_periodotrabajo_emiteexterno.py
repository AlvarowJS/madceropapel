# Generated by Django 3.2.9 on 2022-01-13 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0019_periodotrabajo_emiteexterno'),
    ]

    operations = [
        migrations.AlterField(
            model_name='periodotrabajo',
            name='emiteexterno',
            field=models.BooleanField(default=False, verbose_name='Emite Externo'),
        ),
    ]
