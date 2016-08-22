from django.test import TestCase

from mobetta.forms import TranslationForm

class TranslationFormTests(TestCase):

    def test_clean_success_with_no_format_token(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })

        self.assertTrue(form.is_valid())

    def test_clean_success_with_format_tokens_order_changed(self):
        form = TranslationForm({
            'msgid': "Order is not really {important}, {ok}",
            'translation': "{ok}, l'ordre n'est pas tres {important}.",
            'fuzzy': False,
        })
        self.assertTrue(form.is_valid())

    def test_clean_success_with_format_tokens_source_and_empty_translation(self):
        form = TranslationForm({
            'msgid': "Order is not really {important}, {ok}",
            'translation': "",
            'fuzzy': False,
        })
        self.assertTrue(form.is_valid())

    def test_clean_fail_with_missing_empty_format_token_in_translation(self):
        form = TranslationForm({
            'msgid': "Something to format {}.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_named_format_token_in_translation(self):
        form = TranslationForm({
            'msgid': "Something {important} to format.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_indexed_format_token_in_translation(self):
        form = TranslationForm({
            'msgid': "Something to format {0}.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_empty_format_token_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Rien a formater {}.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_named_format_token_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Rien a formater {actuellement}.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_indexed_format_token_in_source(self):
        form = TranslationForm({
            'msgid': "Nothing to format.",
            'translation': "Ri{1} a formater.",
            'fuzzy': False,
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_clean_fail_with_missing_format_tokens_in_both_source_and_translation(self):
        form = TranslationForm({
            'msgid': "Nothing {important} to format.",
            'translation': "Rien {important} a formater {lol}.",
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
        self.assertIn('{important}', error_message)

    def test_clean_error_display_with_several_tokens(self):
        form = TranslationForm({
            'msgid': "Something {important} to {1} format {}.",
            'translation': "Rien a formater.",
            'fuzzy': False,
        })

        self.assertEqual(len(form.non_field_errors()), 1)

        error_message = form.non_field_errors()[0]
        self.assertIn('{important}', error_message)
        self.assertIn('{1}', error_message)
        self.assertIn('{}', error_message)