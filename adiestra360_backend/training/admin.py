from django.contrib import admin
from .models import TrainingMethods, ExerciseTechniques


@admin.register(TrainingMethods)
class TrainingMethodsAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'motivation_levels')


@admin.register(ExerciseTechniques)
class ExerciseTechniquesAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'method')
    list_filter = ('method',)
