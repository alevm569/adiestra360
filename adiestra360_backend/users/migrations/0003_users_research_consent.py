from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Consentimiento informado para el uso de datos con fines de investigación
    (tesis de maestría). Se captura al registrarse.
    """

    dependencies = [
        ('users', '0002_users_total_xp'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='research_consent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='users',
            name='research_consent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
