from django.contrib import admin
from .models import ExerciseTechniques


@admin.register(ExerciseTechniques)
class ExerciseTechniquesAdmin(admin.ModelAdmin):
    list_display = ('code', 'exercise', 'duracion', 'frecuencia')
    search_fields = ('code', 'exercise__name')
