import os
import shutil

from django.core.management import call_command
from django.test import TestCase

from django.conf import settings

from mobetta.models import TranslationFile
from mobetta.util import update_translations


class POFileTests(TestCase):
    """
    Unit tests for PO file I/O.
    """

    def setUp(self):
        # Copy the example file into django.po
        trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', 'nl', 'LC_MESSAGES')
        shutil.copy(os.path.join(trans_dir, 'django.po.example'), os.path.join(trans_dir, 'django.po'))

        TranslationFile.objects.all().delete()
        call_command('locate_translation_files')

    def test_edit_pofile(self):
        self.assertEqual(TranslationFile.objects.all().count(), 1)

        firstfile = TranslationFile.objects.all().first()
        self.assertEqual(firstfile.filepath, os.path.join(settings.PROJECT_DIR, 'locale', 'nl', 'LC_MESSAGES', 'django.po'))

        pofile = firstfile.get_polib_object()

        msgid_to_change = "String 1"
        current_msgstr = pofile.find(msgid_to_change).msgstr
        self.assertEqual(current_msgstr, u"")

        new_msgstr = "A new string"

        # Make a change to a translation
        changes = [
            {
                'msgid': msgid_to_change, # Original message
                'msgstr': new_msgstr, # New string to use for that message
            }
        ]

        update_translations(pofile, changes)
        pofile.save()

        # Reload the file
        pofile = firstfile.get_polib_object()

        changed_msgstr = pofile.find(msgid_to_change).msgstr
        self.assertEqual(changed_msgstr, new_msgstr)
