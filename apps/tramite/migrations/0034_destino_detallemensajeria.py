# Generated by Django 3.2.9 on 2022-03-03 17:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0033_alter_cargoexterno_ultimoestado'),
    ]

    operations = [
        migrations.AddField(
            model_name='destino',
            name='detallemensajeria',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='destinomensajeria', to='tramite.cargoexternodetalle'),
        ),
    ]