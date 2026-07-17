from django.db import migrations


def rename_forward(apps, schema_editor):
    """
    Nombres correctos según la teoría: 'Llamado' → 'Aquí' y el ejercicio de
    caminar a la pierna → 'Junto'.

    Se limita a los ejercicios de Nivel 1 para no tocar el de Nivel 2
    ('obediencia a la pierna sin collar').
    """
    Exercises = apps.get_model('training', 'Exercises')
    for ex in Exercises.objects.filter(level__name__icontains='Nivel 1'):
        name = (ex.name or '').lower()
        if 'llamado' in name:
            ex.name = 'Aquí'
            ex.save(update_fields=['name'])
        elif 'obediencia' in name or 'pierna' in name:
            ex.name = 'Junto'
            ex.save(update_fields=['name'])


def rename_backward(apps, schema_editor):
    Exercises = apps.get_model('training', 'Exercises')
    for ex in Exercises.objects.filter(level__name__icontains='Nivel 1'):
        name = (ex.name or '').lower()
        if 'aquí' in name or 'aqui' in name:
            ex.name = 'Llamado'
            ex.save(update_fields=['name'])
        elif 'junto' in name:
            ex.name = 'Obediencia pierna'
            ex.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0006_technique_tutorial'),
    ]

    operations = [
        migrations.RunPython(rename_forward, rename_backward),
    ]
