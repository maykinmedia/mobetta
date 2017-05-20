from django.contrib import admin

from .models import TranslationFile


@admin.register(TranslationFile)
class TranslationFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'filepath', 'language_code']
    list_filter = ['language_code', 'is_valid']
