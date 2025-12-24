# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v1', '0011_alter_game_discount_price_alter_game_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='selluser',
            name='balance',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]