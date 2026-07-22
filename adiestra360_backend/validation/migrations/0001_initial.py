import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyResponses',
            fields=[
                ('id', models.CharField(default=uuid.uuid4, max_length=36, primary_key=True, serialize=False)),
                ('q1', models.PositiveSmallIntegerField()),
                ('q2', models.PositiveSmallIntegerField()),
                ('q3', models.PositiveSmallIntegerField()),
                ('q4', models.PositiveSmallIntegerField()),
                ('q5', models.PositiveSmallIntegerField()),
                ('q6', models.PositiveSmallIntegerField()),
                ('q7', models.PositiveSmallIntegerField()),
                ('q8', models.PositiveSmallIntegerField()),
                ('q9', models.PositiveSmallIntegerField()),
                ('q10', models.PositiveSmallIntegerField()),
                ('sus_score', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('is_simulated', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'survey_responses',
            },
        ),
    ]
