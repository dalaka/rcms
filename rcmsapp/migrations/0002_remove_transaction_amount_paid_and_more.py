# Generated by Django 4.2.3 on 2023-08-06 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rcmsapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='amount_paid',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='name',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='tin',
        ),
        migrations.AddField(
            model_name='transaction',
            name='data',
            field=models.JSONField(default=1),
            preserve_default=False,
        ),
    ]
