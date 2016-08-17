import os
import shutil

from django.core.management import call_command
from django.test import TestCase

from django.conf import settings

from mobetta.models import TranslationFile
from mobetta import util


class POFileTests(TestCase):
    """
    Unit tests for PO file I/O.
    """

    def setUp(self):
        # Copy the example file into django.po
        trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', 'nl', 'LC_MESSAGES')
        shutil.copy(os.path.join(trans_dir, 'django.po.example'), os.path.join(trans_dir, 'django.po'))

        self.pofile_path = os.path.join(trans_dir, 'django.po')

        TranslationFile.objects.all().delete()
        call_command('locate_translation_files')

    def tearDown(self):
        os.remove(self.pofile_path)

    def test_edit_translation(self):
        self.assertEqual(TranslationFile.objects.all().count(), 1)

        transfile = TranslationFile.objects.get(filepath=self.pofile_path)
        self.assertEqual(transfile.filepath, self.pofile_path)

        pofile = transfile.get_polib_object()

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

        util.update_translations(pofile, changes)
        pofile.save()

        # Reload the file
        pofile = transfile.get_polib_object()

        changed_msgstr = pofile.find(msgid_to_change).msgstr
        self.assertEqual(changed_msgstr, new_msgstr)

    def test_edit_metadata(self):
        transfile = TranslationFile.objects.get(filepath=self.pofile_path)

        pofile = transfile.get_polib_object()

        util.update_metadata(pofile, 'Test', 'User', 'test@user.nl')
        pofile.save()

        pofile = transfile.get_polib_object()

        expected_metadata = {
            'Last-Translator': u'Test User <test@user.nl>',
            'X-Translated-Using': u'Mobetta {}'.format(util.get_version()),
        }


        for k in expected_metadata.keys():
            self.assertEqual(pofile.metadata[k].decode('utf-8'), expected_metadata[k])
