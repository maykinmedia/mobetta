from django.test import TestCase

from mobetta import util
from mobetta.forms import TranslationForm


class TranslationFormTests(TestCase):

    def test_clean_success_with_no_format_token(self):
        msgid = "Nothing to format."
        form = TranslationForm({
            'msgid': msgid,
            'md5hash': util.get_hash_from_msgid_context(msgid, None),
            'translation': "Rien a formater.",
            'fuzzy': False,
        })

        self.assertTrue(form.is_valid())

    def test_clean_success_with_py3_format_tokens_order_changed(self):
        msgid = "Order is not really {important}, {ok}"
        form = TranslationForm({
            'msgid': msgid,
            'md5hash': util.get_hash_from_msgid_context(msgid, None),
            'translation': "{ok}, l'ordre n'est pas tres {important}.",
            'fuzzy': False,
        })
        self.assertTrue(form.is_valid())

    def test_clean_success_with_py3_format_tokens_source_and_empty_translation(self):
        msgid = "Order is not really {important}, {ok}"
        form = TranslationForm({
            'msgid': msgid,
            'md5hash': util.get_hash_from_msgid_context(msgid, None),
            'translation': "",
            'fuzzy': False,
        })
        self.assertTrue(form.is_valid())

    def test_clean_fail_with_missing_py3_empty_format_token_in_translation(self):
        form = TranslationForm({
            'msgid': "Something to format {}.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py3_named_format_token_in_translation(self):
        form = TranslationForm({
            'msgid': "Something {important} to format.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py3_indexed_format_token_in_translation(self):
        form = TranslationForm({
            'msgid': "Something to format {0}.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py3_empty_format_token_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Rien a formater {}.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py3_named_format_token_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Rien a formater {actuellement}.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py3_indexed_format_token_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Ri{1} a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py3_format_tokens_in_both_source_and_translation(self):
        form = TranslationForm({
            'msgid': "Nothing {important} to format.",
            'translation': "Rien {important} a formater {lol}.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py2_format_token_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Rien a formater %(actuellement)s.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py2_format_token_in_translation(self):
        form = TranslationForm({
            'msgid': "Something %(important)s to format.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_py2_format_tokens_in_both_source_and_translation(self):
        form = TranslationForm({
            'msgid': "Nothing %(important)s to format.",
            'translation': "Rien %(important)s a formater %(lol)s.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_template_variable_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Rien a formater {{ actuellement }}.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_template_variable_in_translation(self):
        form = TranslationForm({
            'msgid': "Something {{ important }} to format.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_template_variables_in_both_source_and_translation(self):
        form = TranslationForm({
            'msgid': "Nothing {{ important }} to format.",
            'translation': "Rien {{ important }} a formater {{ lol }}.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_error_display_with_one_token(self):
        form = TranslationForm({
            'msgid': "Something {important} to format.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertEqual(len(form.non_field_errors()), 1)

        error_message = form.non_field_errors()[0]
        self.assertIn(
            'There should be 1 formating token(s) in the source text and the translation.',
            error_message
        )

    def test_clean_error_display_with_several_tokens(self):
        form = TranslationForm({
            'msgid': "Something {important} to {1} format {}.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })

        self.assertEqual(len(form.non_field_errors()), 1)

        error_message = form.non_field_errors()[0]
        self.assertIn(
            'There should be 3 formating token(s) in the source text and the translation.',
            error_message
        )
