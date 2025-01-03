# Generated by Django 3.2.9 on 2022-03-07 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0034_destino_detallemensajeria'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='documentotipo',
            index=models.Index(fields=['nombre'], name='tramite_doc_nombre_032b06_idx'),
        ),
        migrations.AddIndex(
            model_name='expediente',
            index=models.Index(fields=['anio', 'numero'], name='tramite_exp_anio_91cbe0_idx'),
        ),
        migrations.AddIndex(
            model_name='expediente',
            index=models.Index(fields=['numero'], name='tramite_exp_numero_b61973_idx'),
        ),
    ]
