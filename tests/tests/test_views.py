# coding=utf8

import os
import shutil
from decimal import Decimal

from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf import settings

from .factories import AdminFactory
from .utils import POFileTestCase

from mobetta.models import TranslationFile

from django_webtest import WebTest


def get_field_prefix(form, field_name, value):
    """
    Return the field prefix for the matching 'field_name' and 'value'.

    :param form:       a webtest.forms.Form instance
    :param field_name: a string
    :param value:      a string
    """
    field = next(
        (field for field in form.fields
            if (field is not None) and (field_name in field) and (form[field].value == value))
        , None
    )

    return '-'.join(field.split('-')[:2]) if field else None


class FileDetailViewTests(POFileTestCase, WebTest):

    def setUp(self):
        super(FileDetailViewTests, self).setUp()

        self.admin_user = AdminFactory.create()
        self.url = reverse('file_detail', args=(self.transfile.pk,))

    def test_single_edit(self):
        """
        Go to the file detail view, make an edit to a translation, and submit.
        Check that this translation has changed in the PO file.
        """
        response = self.app.get(self.url, user=self.admin_user)
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
        pofile = self.transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_to_edit).msgstr, new_translation)

        # Check the edit history
        file_edits = self.transfile.edit_logs.all()
        self.assertEqual(file_edits.count(), 1)

        only_file_edit = file_edits.first()
        self.assertEqual(only_file_edit.msgid, msgid_to_edit)
        self.assertEqual(only_file_edit.new_value, new_translation)

    def test_multiple_edits(self):
        """
        Go to the file detail view, make an edit to one translation, one context,
        and one 'fuzzy' attribute. Check that these edits are in the PO file.
        """
        response = self.app.get(self.url, user=self.admin_user)
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
        pofile = self.transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_for_context_edit).msgctxt, new_context)
        self.assertEqual(pofile.find(msgid_for_translation_edit).msgstr, new_translation)
        self.assertIn('fuzzy', pofile.find(msgid_for_fuzzy_edit).flags)

        # Check the edit history
        file_edits = self.transfile.edit_logs.all()
        self.assertEqual(file_edits.count(), 3)

    def test_simultaneous_edits_blocked(self):
        """
        Go to the file detail view as two different users. Make an edit as one of the
        users and submit, then make an edit as the other user and submit.
        The second user's edit should be blocked, and the old_translation field should
        reflect the result of the first user's edit.
        """
        first_user = AdminFactory.create()
        second_user = AdminFactory.create()

        first_user_response = self.app.get(self.url, user=first_user)
        self.assertEqual(first_user_response.status_code, 200)
        second_user_response = self.app.get(self.url, user=second_user)
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

        pofile = self.transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_for_edit).msgstr, first_user_new_translation)

        # Check the edit history: the rejected edit shouldn't be in there
        file_edits = self.transfile.edit_logs.all()
        self.assertEqual(file_edits.count(), 1)

    def test_get_access_if_authenticated(self):
        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

    def test_get_redirect_to_login_page_if_not_authenticated(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login/?next=' + self.url, response['Location'])

    def test_display_translation_error(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        prefix = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix + '-translation'] = 'Un token.'

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="errorlist nonfield"', count=1)

    def test_display_translations_errors(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')
        self.create_poentry(u'An other {important} token', u'Un autre token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        prefix = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix + '-translation'] = 'Un token.'

        prefix = get_field_prefix(form, 'msgid', 'An other {important} token')
        form[prefix + '-translation'] = 'Un autre token.'

        response = form.submit()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="errorlist nonfield"', count=2)

        # Make sure we can still submit the correct value
        form = response.forms['translation-edit']
        form[prefix + '-translation'] = 'Un {important} token'
        response = form.submit()

        self.assertEqual(response.status_code, 200)

    def test_success_to_change_one_fuzzy_field(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.', fuzzy=False)

        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)
        form = response.forms['translation-edit']

        prefix = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix + '-fuzzy'] = True

        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li class="success">Changed 1 translations</li>')

        #form = response.forms['translation-edit']
        #self.assertTrue(form[prefix + '-fuzzy'])

    def test_success_to_change_several_fuzzy_fields(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')
        self.create_poentry(u'An other {important} token', u'Un autre token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        prefix1 = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix1 + '-fuzzy'] = True

        prefix2 = get_field_prefix(form, 'msgid', 'An other {important} token')
        form[prefix2 + '-fuzzy'] = True

        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li class="success">Changed 2 translations</li>')

        #form = response.forms['translation-edit']
        #self.assertTrue(form[prefix1 + '-fuzzy'])
        #self.assertTrue(form[prefix2 + '-fuzzy'])

    def test_success_to_change_one_translation_field(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        prefix1 = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix1 + '-translation'] = 'Un token tres {important}.'

        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li class="success">Changed 1 translations</li>')

        #form = response.forms['translation-edit']
        #self.assertEqual(form[prefix1 + '-translation'].value, 'Un token tres {important}.')

    def test_success_to_change_several_translation_field(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')
        self.create_poentry(u'An other {important} token', u'Un autre token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        prefix1 = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix1 + '-translation'] = 'Un token tres {important}.'

        prefix2 = get_field_prefix(form, 'msgid', 'An other {important} token')
        form[prefix2 + '-translation'] = 'Un autre token tres {important}.'

        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li class="success">Changed 2 translations</li>')

        #form = response.forms['translation-edit']
        #self.assertEqual(form[prefix1 + '-translation'].value, 'Un token tres {important}.')
        #self.assertEqual(form[prefix2 + '-translation'].value, 'Un autre token tres {important}.')

    def test_display_message_if_no_translation_have_been_changed(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<li class="success">Changed 0 translations</li>')

    def test_display_message_if_several_translations_have_been_changed(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')
        self.create_poentry(u'An other {important} token', u'Un autre token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        prefix = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix + '-translation'] = 'Un token tres {important}.'

        prefix = get_field_prefix(form, 'msgid', 'An other {important} token')
        form[prefix + '-translation'] = 'Un autre token tres {important}.'

        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li class="success">Changed 2 translations</li>')


class FileListViewTests(POFileTestCase, WebTest):

    test_pofile_name = 'statstest.po.example'

    def setUp(self):
        super(FileListViewTests, self).setUp()

        self.admin_user = AdminFactory.create()
        self.url = reverse('file_list', kwargs={'lang_code': 'nl'})

    def test_file_stats(self):

        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        soup = response.html
        file_row = soup.find('tr', id="file_detail_{}".format(self.transfile.pk))

        col_titles = ['appname', 'percent_translated', 'total_messages', 'translated', 'fuzzy', 'obsolete', 'filename', 'created']

        stats_cells = file_row.find_all('td', recursive=False)
        stats_results = dict(zip(col_titles, [cell.text for cell in list(stats_cells)]))

        self.assertEqual(Decimal(stats_results['percent_translated']), Decimal(25.0))
        self.assertEqual(int(stats_results['total_messages']), 4)
        self.assertEqual(int(stats_results['translated']), 1)
        self.assertEqual(int(stats_results['fuzzy']), 0)
        self.assertEqual(int(stats_results['obsolete']), 0)
        self.assertEqual(stats_results['filename'], self.pofile_path)

