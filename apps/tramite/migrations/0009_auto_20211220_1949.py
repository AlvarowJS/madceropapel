# Generated by Django 3.2.9 on 2021-12-21 00:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0008_documentotipo_nombrecorto'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='confidencial',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='documento',
            name='confidencialclave',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='documento',
            name='confidencialencriptado',
            field=models.BooleanField(default=False),
        ),
    ]