# Generated by Django 4.1.5 on 2023-01-29 00:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_quote_policy_base'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quote',
            name='policy_base',
        ),
    ]