# Generated by Django 4.2.3 on 2023-07-13 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reddit', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='comment',
            managers=[
            ],
        ),
        migrations.AlterField(
            model_name='comment',
            name='level',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='comment',
            name='lft',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='comment',
            name='rght',
            field=models.PositiveIntegerField(editable=False),
        ),
    ]