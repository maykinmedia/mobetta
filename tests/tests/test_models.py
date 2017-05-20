import os

from django.test import TestCase

from mobetta.models import TranslationFile

from .factories import (
    EditLogFactory, MessageCommentFactory, TranslationFileFactory
)
from .utils import POFileTestCase


class TranslationFileTests(POFileTestCase, TestCase):
    def test_model_name(self):
        translation_file = TranslationFileFactory()
        self.assertEqual(translation_file.model_name, 'path')

    def test_save_mofile_not_a_file(self):
        translation_file = TranslationFileFactory()

        translation_file.save_mofile()
        self.assertFalse(translation_file.is_valid)

    def test_save_mofile(self):
        translation_file = TranslationFile.objects.first()
        mopath = "{}mo".format(translation_file.filepath[:-2])

        if os.path.exists(mopath):
            os.remove(mopath)

        self.assertFalse(os.path.exists(mopath))
        translation_file.save_mofile()
        self.assertTrue(os.path.exists(translation_file.filepath))
        self.assertTrue(translation_file.is_valid)
        self.assertTrue(os.path.exists(mopath))


class EditLogTests(TestCase):
    def test_model_name(self):
        edit_log = EditLogFactory()
        self.assertEqual(edit_log.__unicode__(), '[admin] Field default_fieldname | "default_old_value" -> "default_new_value" in you/shall/not/path')


class MessageCommentTests(TestCase):
    def test_model_name(self):
        message_comment = MessageCommentFactory()
        self.assertEqual(message_comment.__unicode__(), 'Comment by admin on "{}" (nl) at {}'.format(
            message_comment.msghash, message_comment.created.strftime('%d-%m-%Y')))
