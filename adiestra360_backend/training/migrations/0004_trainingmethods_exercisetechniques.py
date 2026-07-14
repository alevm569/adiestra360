import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0003_trainingplanexercises_dominated_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingMethods',
            fields=[
                ('id', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('key', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('motivation_levels', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'training_methods',
            },
        ),
        migrations.CreateModel(
            name='ExerciseTechniques',
            fields=[
                ('id', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('steps', models.TextField(blank=True, null=True)),
                ('tips', models.TextField(blank=True, null=True)),
                ('materials', models.TextField(blank=True, null=True)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.exercises')),
                ('method', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.trainingmethods')),
            ],
            options={
                'db_table': 'exercise_techniques',
                'unique_together': {('exercise', 'method')},
            },
        ),
    ]
