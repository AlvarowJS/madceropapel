# Generated by Django 3.2.9 on 2022-01-21 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0022_documentotipoarea_correlativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodotrabajo',
            name='seguimientocompleto',
            field=models.BooleanField(default=False, verbose_name='Seguimiento Completo'),
        ),
    ]
