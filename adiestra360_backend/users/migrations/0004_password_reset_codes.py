import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Códigos de un solo uso para recuperar la contraseña (se guardan hasheados).
    """

    dependencies = [
        ('users', '0003_users_research_consent'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetCodes',
            fields=[
                ('id', models.CharField(default=uuid.uuid4, max_length=36,
                                        primary_key=True, serialize=False)),
                ('code_hash', models.CharField(max_length=255)),
                ('expires_at', models.DateTimeField()),
                ('attempts', models.IntegerField(default=0)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='password_reset_codes',
                    to='users.users')),
            ],
            options={
                'db_table': 'password_reset_codes',
            },
        ),
        migrations.AddIndex(
            model_name='passwordresetcodes',
            index=models.Index(fields=['user', 'used_at'],
                               name='pwd_reset_user_used_idx'),
        ),
    ]
