# Generated by Django 3.2.9 on 2022-01-14 16:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0009_persona_ultimocargo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personajuridica',
            name='representante',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='inicio.persona', verbose_name='Representante Legal'),
        ),
    ]