# Generated manually for add_sector_email

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0003_remove_nota_notas_nota_numero__5518ab_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sector',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Email'),
        ),
    ]
