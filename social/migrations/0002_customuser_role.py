# Generated by Django 5.1.1 on 2024-09-23 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('read', 'Read'), ('write', 'Write'), ('admin', 'Admin')], default='read', max_length=10),
        ),
    ]
