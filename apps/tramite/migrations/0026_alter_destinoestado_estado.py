# Generated by Django 3.2.9 on 2022-02-14 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0025_alter_documento_observacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destinoestado',
            name='estado',
            field=models.CharField(choices=[('RG', 'Registrado'), ('NL', 'No Leido'), ('LE', 'Leido'), ('RE', 'Recepcionado'), ('RH', 'Rechazado'), ('AT', 'Atendido'), ('AR', 'Archivado'), ('AN', 'Anulado')], default='RG', max_length=2),
        ),
    ]
