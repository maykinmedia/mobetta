import polib

from django.db import models


class TranslationFile(models.Model):

    name = models.CharField(max_length=512, blank=False, null=False)
    filepath = models.CharField(max_length=1024, blank=False, null=False)
    language_code = models.CharField(max_length=32, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.filepath)

    @property
    def model_name(self):
        return app_name_from_filepath(self.filepath)

    def get_polib_object(self):
        return polib.pofile(self.filepath)

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
