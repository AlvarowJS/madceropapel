# Generated by Django 4.0.3 on 2022-04-26 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0058_alter_documento_confidencial'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentotipo',
            name='correlativounico',
            field=models.BooleanField(default=False, verbose_name='Correlativo Único'),
        ),
    ]