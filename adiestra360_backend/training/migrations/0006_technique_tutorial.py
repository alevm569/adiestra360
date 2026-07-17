import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Re-modela las técnicas: el contenido real (teoría Nivel 1) es UN tutorial
    por ejercicio con pasos ordenados, donde algunos pasos tienen una variante
    alternativa (con golosina). Ya no hay 2 métodos globales a elegir.
    El contenido anterior era de ejemplo, así que se recrea la tabla.
    """

    dependencies = [
        ('training', '0005_exercisetechniques_steps_json'),
    ]

    operations = [
        migrations.DeleteModel(name='ExerciseTechniques'),
        migrations.DeleteModel(name='TrainingMethods'),
        migrations.CreateModel(
            name='ExerciseTechniques',
            fields=[
                ('id', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('code', models.CharField(blank=True, max_length=20, null=True)),
                ('objetivo', models.TextField(blank=True, null=True)),
                ('prerrequisito', models.TextField(blank=True, null=True)),
                ('duracion', models.CharField(blank=True, max_length=100, null=True)),
                ('frecuencia', models.CharField(blank=True, max_length=100, null=True)),
                ('competencias', models.JSONField(blank=True, default=list)),
                ('materiales', models.JSONField(blank=True, default=list)),
                ('reglas', models.JSONField(blank=True, default=list)),
                ('steps', models.JSONField(blank=True, default=list)),
                ('errores_comunes', models.JSONField(blank=True, default=list)),
                ('criterio_avanzar', models.JSONField(blank=True, default=list)),
                ('exercise', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='training.exercises')),
            ],
            options={
                'db_table': 'exercise_techniques',
            },
        ),
    ]
