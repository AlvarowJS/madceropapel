# Generated by Django 3.2.9 on 2022-03-07 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0014_auto_20220306_2057'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='cargo',
            index=models.Index(fields=['nombrem'], name='inicio_carg_nombrem_c5173a_idx'),
        ),
        migrations.AddIndex(
            model_name='cargo',
            index=models.Index(fields=['nombref'], name='inicio_carg_nombref_364be9_idx'),
        ),
        migrations.AddIndex(
            model_name='cargo',
            index=models.Index(fields=['nombrecorto'], name='inicio_carg_nombrec_eb61c7_idx'),
        ),
        migrations.AddIndex(
            model_name='distrito',
            index=models.Index(fields=['nombre'], name='inicio_dist_nombre_b62ca5_idx'),
        ),
        migrations.AddIndex(
            model_name='persona',
            index=models.Index(fields=['numero'], name='inicio_pers_numero_4f3b07_idx'),
        ),
        migrations.AddIndex(
            model_name='persona',
            index=models.Index(fields=['nombrecompleto'], name='inicio_pers_nombrec_2742d8_idx'),
        ),
        migrations.AddIndex(
            model_name='persona',
            index=models.Index(fields=['apellidocompleto'], name='inicio_pers_apellid_dfa727_idx'),
        ),
        migrations.AddIndex(
            model_name='personajuridica',
            index=models.Index(fields=['ruc'], name='inicio_pers_ruc_da934a_idx'),
        ),
        migrations.AddIndex(
            model_name='personajuridica',
            index=models.Index(fields=['razonsocial'], name='inicio_pers_razonso_5f7a41_idx'),
        ),
        migrations.AddIndex(
            model_name='personajuridica',
            index=models.Index(fields=['nombrecomercial'], name='inicio_pers_nombrec_ac0906_idx'),
        ),
        migrations.AddIndex(
            model_name='provincia',
            index=models.Index(fields=['nombre'], name='inicio_prov_nombre_cbaa58_idx'),
        ),
        migrations.AddIndex(
            model_name='tipodocumentoidentidad',
            index=models.Index(fields=['nombre'], name='inicio_tipo_nombre_660529_idx'),
        ),
        migrations.AddIndex(
            model_name='tipofirma',
            index=models.Index(fields=['nombre'], name='inicio_tipo_nombre_1c2f9e_idx'),
        ),
    ]