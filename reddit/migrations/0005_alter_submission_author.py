# Generated by Django 4.2.3 on 2023-07-14 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_reddituser_id'),
        ('reddit', '0004_alter_submission_author'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.reddituser'),
        ),
    ]
