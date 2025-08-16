# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('background_content', '0002_add_is_primary_to_background_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='slideshowimage',
            name='is_primary',
            field=models.BooleanField(default=False, help_text='Отметьте, если это основное изображение слайдшоу'),
        ),
    ]