# Generated by Django 5.0.1 on 2024-01-25 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_account_uid'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='is_merchant',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='account',
            name='profile_pic',
            field=models.ImageField(blank=True, default='', null=True, upload_to='profile_pics/'),
        ),
        migrations.AlterField(
            model_name='account',
            name='uid',
            field=models.CharField(default='<function uuid4 at 0x000001A93851FEC0>', max_length=200),
        ),
    ]
