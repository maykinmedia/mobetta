from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ICUConfig(AppConfig):
    name = 'mobetta.icu'
    verbose_name = _("Mobetta ICU")
