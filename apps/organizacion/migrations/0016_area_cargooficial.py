# Generated by Django 3.2.9 on 2021-12-09 15:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0005_cargo_esprincipal'),
        ('organizacion', '0015_alter_periodotrabajo_tipo'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='cargooficial',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='inicio.cargo', verbose_name='Cargo Oficial'),
        ),
    ]