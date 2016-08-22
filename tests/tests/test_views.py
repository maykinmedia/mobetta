# coding=utf8

import os
import shutil
from decimal import Decimal

from django_webtest import WebTest

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf import settings

from mobetta.models import TranslationFile
from tests.app.factory_models import AdminFactory


class FileDetailViewTests(WebTest):

    urls = 'mobetta.urls'

    def setUp(self):
        self.admin_user = AdminFactory.create()

        trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', 'nl', 'LC_MESSAGES')
        shutil.copy(os.path.join(trans_dir, 'django.po.example'), os.path.join(trans_dir, 'django.po'))

        self.pofile_path = os.path.join(trans_dir, 'django.po')
        call_command('locate_translation_files')

    def test_single_edit(self):
        """
        Go to the file detail view, make an edit to a translation, and submit.
        Check that this translation has changed in the PO file.
        """
        self.assertEqual(TranslationFile.objects.all().count(), 1)
        transfile = TranslationFile.objects.all().first()

        url = reverse('file_detail', kwargs={'pk': transfile.pk})

        response = self.app.get(url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        # First string: u'String 1' -> u''
        msgid_to_edit = translation_edit_form['form-0-msgid'].value
        self.assertEqual(translation_edit_form['form-0-translation'].value, u'')

        new_translation = u'Translatèd string'
        translation_edit_form['form-0-translation'] = new_translation
        response = translation_edit_form.submit().follow()
        self.assertEqual(response.status_code, 200)

        # Check the file
        pofile = transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_to_edit).msgstr, new_translation)

    def test_multiple_edits(self):
        """
        Go to the file detail view, make an edit to one translation, one context,
        and one 'fuzzy' attribute. Check that these edits are in the PO file.
        """
        self.assertEqual(TranslationFile.objects.all().count(), 1)
        transfile = TranslationFile.objects.all().first()

        url = reverse('file_detail', kwargs={'pk': transfile.pk})

        response = self.app.get(url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        msgid_for_context_edit = translation_edit_form['form-0-msgid'].value
        self.assertEqual(translation_edit_form['form-0-context'].value, u'')
        new_context = u"A translation cøntext"
        translation_edit_form['form-0-context'] = new_context

        msgid_for_translation_edit = translation_edit_form['form-1-msgid'].value
        self.assertEqual(translation_edit_form['form-1-translation'].value, u'')
        new_translation = u"Another new translatioņ"
        translation_edit_form['form-1-translation'] = new_translation

        msgid_for_fuzzy_edit = translation_edit_form['form-2-msgid'].value
        self.assertEqual(translation_edit_form['form-2-fuzzy'].checked, False)
        new_fuzzy = True
        translation_edit_form['form-2-fuzzy'].checked = new_fuzzy

        response = translation_edit_form.submit().follow()
        self.assertEqual(response.status_code, 200)

        # Check the file
        pofile = transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_for_context_edit).msgctxt, new_context)
        self.assertEqual(pofile.find(msgid_for_translation_edit).msgstr, new_translation)
        self.assertIn('fuzzy', pofile.find(msgid_for_fuzzy_edit).flags)

    def test_simultaneous_edits_blocked(self):
        """
        Go to the file detail view as two different users. Make an edit as one of the
        users and submit, then make an edit as the other user and submit.
        The second user's edit should be blocked, and the old_translation field should
        reflect the result of the first user's edit.
        """
        self.assertEqual(TranslationFile.objects.all().count(), 1)
        transfile = TranslationFile.objects.all().first()

        first_user = AdminFactory.create()
        second_user = AdminFactory.create()

        url = reverse('file_detail', kwargs={'pk': transfile.pk})

        first_user_response = self.app.get(url, user=first_user)
        self.assertEqual(first_user_response.status_code, 200)
        second_user_response = self.app.get(url, user=second_user)
        self.assertEqual(second_user_response.status_code, 200)

        id_field_id_to_edit = 'form-0-msgid'
        trans_field_id_to_edit = 'form-0-translation'
        old_trans_field_id_to_edit = 'form-0-old_translation'

        # Make the edit as the first user
        first_user_edit_form = first_user_response.forms['translation-edit']
        msgid_for_edit = first_user_edit_form[id_field_id_to_edit].value
        trans_for_edit = first_user_edit_form[trans_field_id_to_edit].value
        first_user_new_translation = u"First user translation"
        first_user_edit_form[trans_field_id_to_edit] = first_user_new_translation
        first_user_response = first_user_edit_form.submit().follow()
        self.assertEqual(first_user_response.status_code, 200)

        # Try to make a similar edit as the second user
        second_user_edit_form = second_user_response.forms['translation-edit']
        self.assertEqual(second_user_edit_form[id_field_id_to_edit].value, msgid_for_edit)
        self.assertEqual(second_user_edit_form[trans_field_id_to_edit].value, trans_for_edit)
        second_user_edit_form[trans_field_id_to_edit] = u"Second user translation"
        second_user_response = second_user_edit_form.submit()
        expected_err_msg = _("The %s for \"%s\" was edited while you were editing it") \
                            % ("translation", msgid_for_edit)
        expected_err_msg = _("This value was edited while you were editing it (new value: %s)") \
                            % (first_user_new_translation)
        self.assertIn(expected_err_msg, second_user_response.text)

        # The old_translation in the form should now reflect the first user's translation
        second_user_edit_form = second_user_response.forms['translation-edit']
        self.assertEqual(second_user_edit_form[old_trans_field_id_to_edit].value, first_user_new_translation)

        pofile = transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_for_edit).msgstr, first_user_new_translation)


class FileListViewTests(WebTest):

    urls = 'mobetta.urls'

    def setUp(self):
        self.admin_user = AdminFactory.create()

        trans_dir = os.path.join(settings.PROJECT_DIR, 'locale', 'nl', 'LC_MESSAGES')
        shutil.copy(os.path.join(trans_dir, 'statstest.po.example'), os.path.join(trans_dir, 'django.po'))

        self.pofile_path = os.path.join(trans_dir, 'django.po')
        call_command('locate_translation_files')

    def test_file_stats(self):
        self.assertEqual(TranslationFile.objects.all().count(), 1)
        transfile = TranslationFile.objects.all().first()

        url = reverse('file_list')

        response = self.app.get(url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        soup = response.html
        file_row = soup.find('tr', id="file_detail_{}".format(transfile.pk))

        col_titles = ['appname', 'percent_translated', 'total_messages', 'translated', 'fuzzy', 'obsolete', 'filename', 'created']

        stats_cells = file_row.find_all('td', recursive=False)
        stats_results = dict(zip(col_titles, [cell.text for cell in list(stats_cells)]))

        self.assertEqual(Decimal(stats_results['percent_translated']), Decimal(25.0))
        self.assertEqual(int(stats_results['total_messages']), 4)
        self.assertEqual(int(stats_results['translated']), 1)
        self.assertEqual(int(stats_results['fuzzy']), 0)
        self.assertEqual(int(stats_results['obsolete']), 0)
        self.assertEqual(stats_results['filename'], self.pofile_path)
