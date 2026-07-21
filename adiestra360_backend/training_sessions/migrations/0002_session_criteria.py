from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Guarda el checklist de criterio_avanzar por sesión: cuántos criterios se
    cumplieron (criteria_met) de un total (criteria_total). De ahí se derivan
    el resultado (reforzar/bien/excelente) y la regla de superado.
    """

    dependencies = [
        ('training_sessions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingsessions',
            name='criteria_met',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trainingsessions',
            name='criteria_total',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
