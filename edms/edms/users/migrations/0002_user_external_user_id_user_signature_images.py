# Generated by Django 5.0.8 on 2024-10-03 02:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0004_alter_asset_file_type'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='external_user_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='signature_images',
            field=models.ManyToManyField(related_name='signature_assets', to='assets.asset'),
        ),
    ]
