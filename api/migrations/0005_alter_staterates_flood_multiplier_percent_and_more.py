# Generated by Django 4.1.5 on 2023-01-29 00:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_remove_quote_policy_base'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staterates',
            name='flood_multiplier_percent',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='staterates',
            name='monthly_tax_percent',
            field=models.FloatField(),
        ),
    ]
