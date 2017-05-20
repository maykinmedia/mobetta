"""
Translation file models, specific to ICU format files.
"""
from __future__ import absolute_import, unicode_literals

import json
import os
from collections import OrderedDict

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from ..models import BaseEditLog, BaseMessageComment
from ..validators import validate_filepath_exists


class IcuFile(object):

    def __init__(self, path):
        self.path = path
        with open(self.path) as infile:
            self.contents = json.load(infile, object_pairs_hook=OrderedDict)

    def __iter__(self):
        return iter(self.contents.items())

    @property
    def total_messages(self):
        return len(self.contents)

    @property
    def translated_entries(self):
        # TODO
        return self

    @property
    def untranslated_entries(self):
        # TODO
        return self

    def save(self):
        with open(self.path, 'w') as outfile:
            json.dump(self.contents, outfile)


@python_2_unicode_compatible
class ICUTranslationFile(models.Model):
    name = models.CharField(max_length=512, blank=False)
    filepath = models.CharField(
        max_length=1024, blank=False,
        validators=[validate_filepath_exists]
    )
    language_code = models.CharField(
        max_length=32, choices=settings.LANGUAGES,
        blank=False, editable=False
    )

    created = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("ICU translation file")
        verbose_name_plural = _("ICU translation files")

    def __str__(self):
        return "{}: {}".format(
            self.name,
            os.path.basename(self.filepath)
        )

    def save(self, *args, **kwargs):
        self.language_code = self._get_language_code()
        super(ICUTranslationFile, self).save(*args, **kwargs)

    def _get_language_code(self):
        return os.path.splitext(os.path.basename(self.filepath))[0].lower()

    def get_language_name(self):
        return dict(settings.LANGUAGES)[self.language_code]

    def get_icufile_object(self):
        if not hasattr(self, '_icu_file'):
            self._icu_file = IcuFile(self.filepath)
        return self._icu_file

    def get_statistics(self):
        icu_file = self.get_icufile_object()
        return {
            'total_messages': icu_file.total_messages,
        }


class EditLog(BaseEditLog):
    file_edited = models.ForeignKey(
        ICUTranslationFile, blank=False, null=False, related_name='edit_logs'
    )


class MessageComment(BaseMessageComment):
    translation_file = models.ForeignKey(
        ICUTranslationFile, blank=False,
        null=False, related_name='comments'
    )
