from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.conf import settings
from django.db.models import Count

from ..access import can_translate_language
from .models import ICUTranslationFile


class ICULanguageListMixin(object):

    def is_enabled(self):
        return apps.is_installed('mobetta.icu')

    def get_icu_languages(self):
        names = dict(settings.LANGUAGES)
        translation_files = (
            ICUTranslationFile.objects
            .values_list('language_code').annotate(count=Count('*'))
        )
        return [
            (code, names[code], count) for code, count in translation_files
            if can_translate_language(self.request.user, code)
        ]

    def get_context_data(self, **kwargs):
        context = super(ICULanguageListMixin, self).get_context_data(**kwargs)
        if self.is_enabled():
            context['icu_languages'] = self.get_icu_languages()
        return context
