# Generated by Django 3.2.6 on 2021-11-15 18:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0001_initial'),
        ('organizacion', '0004_alter_area_documentosustento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='area',
            name='documentosustento',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='tramite.documento', verbose_name='Documento Sustento'),
        ),
    ]