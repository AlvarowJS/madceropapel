# Generated by Django 4.0.3 on 2022-03-21 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0041_remove_documentotipo_forma_documentotipo_tieneforma'),
    ]

    operations = [
        migrations.AddField(
            model_name='documento',
            name='forma',
            field=models.CharField(choices=[('I', 'Individual'), ('L', 'Listado')], default='I', max_length=1, verbose_name='Forma'),
        ),
    ]