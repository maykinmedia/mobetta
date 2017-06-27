from django.apps import apps

if apps.is_installed('mobetta.icu'):
    from .icu.mixins import ICULanguageListMixin
else:
    class ICULanguageListMixin(object):
        pass
