# Generated by Django 3.2.9 on 2022-02-04 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0024_alter_destinoestado_observacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documento',
            name='observacion',
            field=models.TextField(blank=True, max_length=500, null=True, verbose_name='Observación'),
        ),
    ]
