# Generated by Django 4.0.3 on 2022-03-18 17:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0027_auto_20220306_2113'),
        ('tramite', '0038_alter_destino_mesapartesmodoenvio'),
    ]

    operations = [
        migrations.AddField(
            model_name='distribuidor',
            name='arearindente',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organizacion.area'),
        ),
        migrations.AlterField(
            model_name='destinoestadomensajeria',
            name='estado',
            field=models.CharField(choices=[('PE', 'Pendiente'), ('RA', 'Recibido Automático'), ('RM', 'Recibido Manual'), ('DA', 'Devuelto Automático'), ('DM', 'Devuelto Manual'), ('GN', 'Generado'), ('EN', 'Enviado'), ('FI', 'Finalizado'), ('FD', 'Finalizado Directo'), ('NE', 'No Entregado'), ('AR', 'Archivado')], default='PE', max_length=2),
        ),
    ]