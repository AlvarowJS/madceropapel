# Generated by Django 3.2.9 on 2021-12-21 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0009_auto_20211220_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='personajuridicatipo',
            field=models.CharField(choices=[('R', 'RUC'), ('O', 'OTRO')], default='R', max_length=1, verbose_name='Tipo Persona Jurídica'),
        ),
    ]
