# Generated by Django 4.1.5 on 2023-01-29 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_rename_base_rate_quote_policy_base_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quote',
            name='policy_base',
            field=models.FloatField(default=0.0),
        ),
    ]