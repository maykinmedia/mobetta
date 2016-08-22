import os
import shutil

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from mobetta.models import TranslationFile

from polib import POEntry

class POFileTestCase(TestCase):
    """
    Base class that creates a new copy of a .po file before each test
    and destroy it after each test.
    """
    def setUp(self):
        # Copy the example file into django.po
        trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', 'nl', 'LC_MESSAGES')
        shutil.copy(os.path.join(trans_dir, 'django.po.example'), os.path.join(trans_dir, 'django.po'))

        self.pofile_path = os.path.join(trans_dir, 'django.po')

        TranslationFile.objects.all().delete()
        call_command('locate_translation_files')

        self.transfile = TranslationFile.objects.get(filepath=self.pofile_path)

    def tearDown(self):
        os.remove(self.pofile_path)

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



