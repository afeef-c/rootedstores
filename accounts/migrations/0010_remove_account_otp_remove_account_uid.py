# Generated by Django 5.0.1 on 2024-01-27 06:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_account_uid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='account',
            name='otp',
        ),
        migrations.RemoveField(
            model_name='account',
            name='uid',
        ),
    ]
