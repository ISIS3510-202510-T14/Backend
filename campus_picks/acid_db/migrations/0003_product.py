from django.db import migrations, models
import uuid

class Migration(migrations.Migration):

    dependencies = [
        ('acid_db', '0002_alter_team_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('product_id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('image_url', models.CharField(max_length=255, blank=True)),
                ('category', models.CharField(max_length=100, blank=True)),
            ],
        ),
    ]
