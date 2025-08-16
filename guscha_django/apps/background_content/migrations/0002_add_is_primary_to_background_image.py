# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('background_content', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='backgroundimage',
            name='is_primary',
            field=models.BooleanField(default=False, help_text='Отметьте, если это основное изображение для отображения'),
        ),
    ]