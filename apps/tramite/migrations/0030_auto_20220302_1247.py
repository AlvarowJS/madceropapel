# Generated by Django 3.2.9 on 2022-03-02 17:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0026_auto_20220127_1823'),
        ('tramite', '0029_auto_20220301_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='cargoexterno',
            name='dependencia',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, to='organizacion.dependencia'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cargoexterno',
            name='emisor',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, to='organizacion.periodotrabajo'),
            preserve_default=False,
        ),
    ]
