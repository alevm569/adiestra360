from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dogs', '0002_dogs_reinforcement_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='dogs',
            name='photo',
            field=models.TextField(blank=True, null=True),
        ),
    ]
