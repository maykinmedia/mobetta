from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .models import ICUTranslationFile


@admin.register(ICUTranslationFile)
class ICUTranslationFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'filepath', 'language_code']
    list_filter = ['language_code']
