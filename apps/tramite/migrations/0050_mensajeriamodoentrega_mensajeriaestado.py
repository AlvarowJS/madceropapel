# Generated by Django 4.0.3 on 2022-03-25 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0049_destino_mensajeriamodoentrega'),
    ]

    operations = [
        migrations.AddField(
            model_name='mensajeriamodoentrega',
            name='mensajeriaestado',
            field=models.CharField(default='PE', max_length=2),
        ),
    ]