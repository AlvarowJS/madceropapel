# Generated by Django 3.2.6 on 2021-11-15 17:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0001_initial'),
        ('organizacion', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='documentosustento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='comisiones', to='tramite.documento', verbose_name='Documento Sustento'),
        ),
    ]
