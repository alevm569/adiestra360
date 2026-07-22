from django.contrib import admin

from .models import SurveyResponses


@admin.register(SurveyResponses)
class SurveyResponsesAdmin(admin.ModelAdmin):
    list_display = ('user', 'sus_score', 'is_simulated', 'created_at')
    list_filter = ('is_simulated',)
    readonly_fields = ('sus_score', 'created_at', 'updated_at')
