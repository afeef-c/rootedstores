# Generated by Django 5.0.1 on 2024-01-30 03:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_alter_account_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='uid',
            field=models.CharField(default='<function uuid4 at 0x0000029D1CA81C60>', max_length=200),
        ),
    ]
