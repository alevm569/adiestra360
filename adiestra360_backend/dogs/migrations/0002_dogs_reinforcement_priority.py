from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dogs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dogs',
            name='reinforcement_priority',
            field=models.TextField(blank=True, null=True),
        ),
    ]
