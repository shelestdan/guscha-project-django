# Generated manually

import apps.products.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_update_product_image_validators'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreorderImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('image', models.ImageField(blank=True, help_text='Поддерживаемые форматы: JPG, JPEG, PNG, WebP, GIF. Максимальный размер: 5MB. Минимальный размер: 100x100px.', null=True, upload_to=apps.products.models.preorder_image_upload_path, validators=[apps.products.models.validate_image_file, django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'], message='Поддерживаемые форматы: JPG, JPEG, PNG, WebP, GIF')], verbose_name='Изображение')),
                ('image_url', models.URLField(blank=True, help_text='Альтернатива загрузке файла - укажите прямую ссылку на изображение', max_length=500, verbose_name='URL изображения')),
                ('alt_text', models.CharField(blank=True, help_text='Описание изображения для поисковых систем и доступности', max_length=255, null=True, verbose_name='Alt текст')),
                ('is_primary', models.BooleanField(default=False, help_text='Отметьте для установки в качестве основного изображения предзаказа', verbose_name='Основное изображение')),
                ('sort_order', models.IntegerField(blank=True, default=0, help_text='Порядок отображения (меньшее число = выше в списке)', verbose_name='Порядок сортировки')),
                ('preorder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preorder_images', to='products.preorder', verbose_name='Предзаказ')),
            ],
            options={
                'verbose_name': 'Изображение предзаказа',
                'verbose_name_plural': 'Изображения предзаказов',
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]