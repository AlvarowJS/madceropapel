# Generated by Django 3.2.9 on 2022-03-03 15:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0032_auto_20220303_1032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cargoexterno',
            name='ultimoestado',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ultimoestado', to='tramite.cargoexternoestado'),
        ),
    ]
