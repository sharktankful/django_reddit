# Generated by Django 4.2.3 on 2023-07-14 12:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_reddituser_id'),
        ('reddit', '0003_alter_comment_id_alter_submission_id_alter_vote_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='author',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='users.reddituser'),
        ),
    ]