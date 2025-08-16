# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('background_content', '0003_add_is_primary_to_slideshowimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='slideshowimage',
            name='width',
            field=models.PositiveIntegerField(null=True, blank=True, verbose_name='Ширина'),
        ),
        migrations.AddField(
            model_name='slideshowimage',
            name='height',
            field=models.PositiveIntegerField(null=True, blank=True, verbose_name='Высота'),
        ),
    ]