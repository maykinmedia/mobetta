import os
import shutil

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from polib import POEntry

from mobetta.models import TranslationFile


class POFileTestCase(TestCase):
    """
    Base class that creates a new copy of a .po file before each test
    and destroy it after each test.

    Only one language (Dutch) is used here.
    """

    test_pofile_name = 'django.po.example'

    def setUp(self):
        # Copy the example file into django.po
        pofiles_dir = os.path.join(settings.PROJECT_DIR, 'pofiles')
        trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', 'nl', 'LC_MESSAGES')

        shutil.copy(os.path.join(pofiles_dir, self.test_pofile_name), os.path.join(trans_dir, 'django.po'))

        self.pofile_path = os.path.join(trans_dir, 'django.po')

        TranslationFile.objects.all().delete()
        call_command('locate_translation_files')

        self.transfile = TranslationFile.objects.get(filepath=self.pofile_path)

    def tearDown(self):
        os.remove(self.pofile_path)

        TranslationFile.objects.all().delete()

    def create_poentry(self, source, translation='', fuzzy=False):
        entry = POEntry(
            msgid=source,
            msgstr=translation,
        )

        if fuzzy:
            entry.flags.append('fuzzy')

        po = self.transfile.get_polib_object()
        po.append(entry)
        po.save(self.pofile_path)


class MultiplePOFilesTestCase(TestCase):
    """
    Base class that creates multiple PO files in different languages.

    `test_pofiles` is a list of tuples of (<filename>, <language_code>).
    """

    def setUp(self):
        pofiles_dir = os.path.join(settings.PROJECT_DIR, 'pofiles')

        for filename, language_code in self.test_pofiles:
            trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', language_code, 'LC_MESSAGES')
            if not os.path.exists(trans_dir):
                os.makedirs(trans_dir)

            shutil.copy(os.path.join(pofiles_dir, filename), os.path.join(trans_dir, 'django.po'))

        TranslationFile.objects.all().delete()
        call_command('locate_translation_files')

    def tearDown(self):
        for filename, language_code in self.test_pofiles:
            trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', language_code, 'LC_MESSAGES')
            os.remove(os.path.join(trans_dir, 'django.po'))

        TranslationFile.objects.all().delete()
