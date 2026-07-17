import uuid
from django.db import migrations

import training.fields


class Migration(migrations.Migration):
    """
    Alinea los ids con el esquema real: CHAR(36) en vez de VARCHAR(36).

    La BD se creó con SQL a mano usando char(36); Django generaba varchar(36).
    Con la collation NO PAD de MySQL 8, una FK varchar→char nunca hace match y
    falla al insertar (error 1452). Eso rompía exercise_techniques.

    Al cambiar el tipo del PK de Exercises, Django ajusta también las columnas
    FK que lo apuntan. En tu BD, exercises/training_plan_exercises/
    training_sessions ya son char(36) (los ALTER son no-ops); el cambio real es
    exercise_techniques.exercise_id → char(36).
    """

    dependencies = [
        ('training', '0007_rename_exercises_aqui_junto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercises',
            name='id',
            field=training.fields.CharUUIDField(
                default=uuid.uuid4, max_length=36, primary_key=True, serialize=False
            ),
        ),
        migrations.AlterField(
            model_name='exercisetechniques',
            name='id',
            field=training.fields.CharUUIDField(
                default=uuid.uuid4, max_length=36, primary_key=True, serialize=False
            ),
        ),
    ]
