# -*- coding: utf-8 -*-
import re
from unittest import TestCase

from mobetta import util
from mobetta.models import TranslationFile
from mobetta.util import get_token_regexes

from .utils import POFileTestCase


class TokenRegexTests(TestCase):
    """
    Unit test the token highlighting machinery.
    """
    regex = re.compile('|'.join(get_token_regexes()))

    def test_old_format(self):
        test_string = 'foo %(bar) baz'
        tokens = self.regex.findall(test_string)
        self.assertEqual(tokens, [])

        valid = 'acdefgiorsux'
        for modifier in valid:
            test_string = 'foo %(bar)' + modifier + ' baz'
            tokens = self.regex.findall(test_string)
            self.assertEqual(tokens, ['%(bar)' + modifier])

        invalid = 'bhjklmnpqtvwyz'
        for modifier in invalid:
            test_string = 'foo %(bar)' + modifier + ' baz'
            tokens = self.regex.findall(test_string)
            self.assertEqual(tokens, [])


class POFileTests(POFileTestCase):
    """
    Unit tests for PO file I/O.
    """

    def test_edit_translation(self):
        self.assertEqual(TranslationFile.objects.all().count(), 1)

        transfile = TranslationFile.objects.get(filepath=self.pofile_path)
        self.assertEqual(transfile.filepath, self.pofile_path)

        pofile = transfile.get_polib_object()

        msgid_to_change = u"String 1"
        poentry = pofile.find(msgid_to_change)
        current_msgstr = poentry.msgstr
        initial_value = u""
        self.assertEqual(current_msgstr, initial_value)

        new_msgstr = u"A nĕw Štring"

        """
        Format of changes:
        [
            (<form>, [
                {
                'msgid': <msgid>,
                'md5hash': <hash>,
                'field': '<field_name>',
                'from': '<old_value>',
                'to': '<new_value>',
                },
                ...
            ]),
            ...
        ]
        """

        # Make a change to a translation
        changes = [
            (None, [
                {
                    'msgid': msgid_to_change,  # Original message
                    'md5hash': util.get_message_hash(poentry),
                    'field': 'translation',  # Field to change
                    'from': initial_value,
                    'to': new_msgstr,  # New string to use for that message
                },
            ]),
        ]

        applied_changes, rejected_changes = util.update_translations(pofile, changes)

        self.assertEqual(len(applied_changes), 1)
        self.assertEqual(len(rejected_changes), 0)

        pofile.save()

        # Reload the file
        pofile = transfile.get_polib_object()

        changed_msgstr = pofile.find(msgid_to_change).msgstr
        self.assertEqual(changed_msgstr, new_msgstr)

    def test_edit_metadata(self):
        transfile = TranslationFile.objects.get(filepath=self.pofile_path)

        pofile = transfile.get_polib_object()

        # Use unicode in name to test unicode handling
        util.update_metadata(pofile, u'Ŧest', u'User', u'test@user.nl')
        pofile.save()

        pofile = transfile.get_polib_object()

        self.assertEqual(pofile.metadata['Last-Translator'], u'Ŧest User <test@user.nl>')

        version_code = u'Mobetta {}'.format(util.get_version())
        self.assertEqual(pofile.metadata['X-Translated-Using'], version_code)
