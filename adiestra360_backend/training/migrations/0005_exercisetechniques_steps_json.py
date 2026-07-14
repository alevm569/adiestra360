from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0004_trainingmethods_exercisetechniques'),
    ]

    operations = [
        # Se recrea el campo (era TextField) como JSON para soportar pasos con
        # imagen. Contenido previo era de ejemplo, así que no hay pérdida real.
        migrations.RemoveField(
            model_name='exercisetechniques',
            name='steps',
        ),
        migrations.AddField(
            model_name='exercisetechniques',
            name='steps',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
