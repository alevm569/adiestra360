from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0002_alter_trainingplans_current_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingplanexercises',
            name='dominated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='trainingplanexercises',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
