from __future__ import absolute_import, unicode_literals

import os.path

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

import polib

from .util import app_name_from_filepath

# UserModel represents the model used by the project
UserModel = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


@python_2_unicode_compatible
class TranslationFile(models.Model):
    name = models.CharField(max_length=512, blank=False, null=False)
    filepath = models.CharField(max_length=1024, blank=False, null=False)
    language_code = models.CharField(max_length=32, choices=settings.LANGUAGES, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    last_compiled = models.DateTimeField(null=True)
    is_valid = models.BooleanField(default=True)

    def __str__(self):
        return "{} ({})".format(self.name, self.filepath)

    @property
    def model_name(self):
        return app_name_from_filepath(self.filepath)

    def get_polib_object(self):
        return polib.pofile(self.filepath)

    def save_mofile(self):
        if os.path.isfile(self.filepath):
            pofile = polib.pofile(self.filepath)
            mopath = "{}mo".format(self.filepath[:-2])
            pofile.save_as_mofile(mopath)
            self.last_compiled = timezone.now()
        else:
            self.is_valid = False
        self.save()

    def get_statistics(self):
        """
        Return statistics for this file:
        - % translated
        - total messages
        - messages translated
        - fuzzy messages
        - obsolete messages
        """
        pofile = self.get_polib_object()

        translated_entries = len(pofile.translated_entries())
        untranslated_entries = len(pofile.untranslated_entries())
        fuzzy_entries = len(pofile.fuzzy_entries())
        obsolete_entries = len(pofile.obsolete_entries())

        return {
            'percent_translated': pofile.percent_translated(),
            'total_messages': translated_entries + untranslated_entries,
            'translated_messages': translated_entries,
            'fuzzy_messages': fuzzy_entries,
            'obsolete_messages': obsolete_entries,
        }

    def get_language_name(self):
        return dict(settings.LANGUAGES)[self.language_code]


class BaseEditLog(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserModel, related_name='%(app_label)s_%(class)ss')
    msgid = models.TextField()

    msghash = models.CharField(max_length=32, null=False, blank=False)
    """
    ``msghash`` is an md5 hash of the msgid and msgctxt, using util.get_hash_from_msgid_context.
    """

    fieldname = models.CharField(max_length=127, blank=False, null=False)
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ['created']

    def __unicode__(self):
        return u"[{}] Field {} | \"{}\" -> \"{}\" in {}".format(
            str(self.user),
            self.fieldname,
            self.old_value,
            self.new_value,
            self.file_edited.filepath,
        )


class EditLog(BaseEditLog):
    file_edited = models.ForeignKey(TranslationFile, blank=False, null=False, related_name='edit_logs')


class BaseMessageComment(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(UserModel, related_name='%(app_label)s_%(class)ss')

    msghash = models.CharField(max_length=32, null=False, blank=False)
    """
    ``msghash`` is an md5 hash of the msgid and msgctxt, using util.get_hash_from_msgid_context.
    """

    body = models.CharField(max_length=1024, blank=False, null=False)

    class Meta:
        abstract = True
        ordering = ['created']

    def __unicode__(self):
        return u"Comment by {} on \"{}\" ({}) at {}".format(
            str(self.user),
            self.msghash,
            self.translation_file.language_code,
            self.created.strftime('%d-%m-%Y')
        )


class MessageComment(BaseMessageComment):
    translation_file = models.ForeignKey(TranslationFile, blank=False, null=False, related_name='comments')
