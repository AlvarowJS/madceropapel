# Generated by Django 3.2.9 on 2021-12-22 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0011_alter_documento_personajuridicatipo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documento',
            name='ciudadanocargo',
            field=models.CharField(blank=True, default='', max_length=150, verbose_name='Cargo'),
        ),
    ]