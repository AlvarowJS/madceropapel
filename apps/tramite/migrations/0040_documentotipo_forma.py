# Generated by Django 4.0.3 on 2022-03-21 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramite', '0039_distribuidor_arearindente_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentotipo',
            name='forma',
            field=models.CharField(choices=[('A', 'Automática'), ('M', 'Manual')], default='A', max_length=1, verbose_name='Forma'),
        ),
    ]