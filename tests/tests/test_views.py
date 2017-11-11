# coding=utf8
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest

from mobetta.models import TranslationFile
from mobetta.util import get_hash_from_msgid_context

from .factories import AdminFactory, EditLogFactory, UserFactory
from .utils import MultiplePOFilesTestCase, POFileTestCase


def get_field_prefix(form, field_name, value):
    """
    Return the field prefix for the matching 'field_name' and 'value'.

    :param form:       a webtest.forms.Form instance
    :param field_name: a string
    :param value:      a string
    """
    field = next(
        (field for field in form.fields
         if (field is not None) and (field_name in field) and (form[field].value == value)), None)

    return '-'.join(field.split('-')[:2]) if field else None


class CompilePoFilesViewTests(POFileTestCase, WebTest):
    def setUp(self):
        super(CompilePoFilesViewTests, self).setUp()

        self.admin_user = AdminFactory.create()
        self.user = UserFactory.create()
        self.url = reverse('mobetta:compile_po_files')

    def test_login_required(self):
        self.app.get(self.url, status=302)

    def test_no_permission(self):
        self.app.get(self.url, user=self.user, status=302)

    def test_compile_files(self):
        self.app.get(self.url, user=self.admin_user, status=302)


class FindPoFilesViewTests(POFileTestCase, WebTest):
    def setUp(self):
        super(FindPoFilesViewTests, self).setUp()

        self.admin_user = AdminFactory.create()
        self.user = UserFactory.create()
        self.url = reverse('mobetta:find_po_files')

    def test_login_required(self):
        self.app.get(self.url, status=302)

    def test_no_permission(self):
        self.app.get(self.url, user=self.user, status=302)

    def test_compile_files(self):
        self.app.get(self.url, user=self.admin_user, status=302)


class FileDetailViewTests(POFileTestCase, WebTest):

    def setUp(self):
        super(FileDetailViewTests, self).setUp()

        self.admin_user = AdminFactory.create()
        self.user = UserFactory.create()
        self.url = reverse('mobetta:file_detail', args=(self.transfile.pk,))

    def test_login_required(self):
        self.app.get(self.url, status=302)

    def test_no_permission(self):
        self.app.get(self.url, user=self.user, status=403)

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
        msghash_to_edit = get_hash_from_msgid_context(msgid_to_edit, '')
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
        self.assertEqual(only_file_edit.msghash, msghash_to_edit)
        self.assertEqual(only_file_edit.new_value, new_translation)

    def test_multiple_edits(self):
        """
        Go to the file detail view, make an edit to one translation
        and one 'fuzzy' attribute. Check that these edits are in the PO file.
        """
        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        msgid_for_translation_edit = translation_edit_form['form-1-msgid'].value
        self.assertEqual(translation_edit_form['form-1-translation'].value, u'Translation of string 2')
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
        self.assertEqual(pofile.find(msgid_for_translation_edit).msgstr, new_translation)
        self.assertIn('fuzzy', pofile.find(msgid_for_fuzzy_edit).flags)

        # Check the edit history
        file_edits = self.transfile.edit_logs.all()
        self.assertEqual(file_edits.count(), 2)

    def test_multiline_edit(self):
        """
        Edit the multi-line string in django.po.example.
        """
        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        # The multiline string is the 5th one in the file.
        msgid_to_edit = translation_edit_form['form-4-msgid'].value

        # The new message has newlines and whitespace on both sides. Prevent this from
        # being stripped off!
        new_translation = u'Now with even\nmore\nlines\n(and tokens: %(start)s %(end)s %(count)s)'
        translation_edit_form['form-4-translation'] = new_translation
        response = translation_edit_form.submit().follow()
        self.assertEqual(response.status_code, 200)

        # Check the file
        pofile = self.transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_to_edit).msgstr, new_translation)

        # Check the edit history
        file_edits = self.transfile.edit_logs.all()
        self.assertEqual(file_edits.count(), 1)

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
        expected_err_msg = _("This value was edited while you were editing it "
                             "(new value: %s)") % first_user_new_translation
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

    def test_token_error_with_simultaneous_edit(self):
        """
        This issue is outlined in issue #28. Follow this sequence of events:

        - User1 loads the FileListView
        - User2 loads the FileListView
        - User1 edits a translation with a token (the translation still contains
            the token, and is valid).
        - User2 edits the same translation without reloading. User2 forgets to
            add the token to the translation.
        - User2 gets the 'token not found' error, and amends their translation
            to include the token.
        - At this point, the system used to give a 'multiple edits' error, since the
            old_translation value hadn't been updated after the first error. Now
            the translation should be changed successfully.
        """
        self.create_poentry(u'An {important} token', u'')

        user1 = AdminFactory.create()
        user2 = AdminFactory.create()

        response_user1 = self.app.get(self.url, user=user1)
        response_user2 = self.app.get(self.url, user=user2)

        form_user1 = response_user1.forms['translation-edit']
        prefix = get_field_prefix(form_user1, 'msgid', 'An {important} token')
        form_user1[prefix + '-translation'] = u'Un {important} token'
        response_user1 = form_user1.submit().follow()
        self.assertEqual(response_user1.status_code, 200)

        form_user2 = response_user2.forms['translation-edit']
        prefix = get_field_prefix(form_user2, 'msgid', 'An {important} token')
        form_user2[prefix + '-translation'] = u'Un token'
        response_user2 = form_user2.submit()
        self.assertEqual(response_user2.status_code, 200)
        self.assertIn(
            'There should be 1 formating token(s) in the source text and the translation.',
            response_user2.text,
        )

        # Now change the translation to include the token
        form_user2 = response_user2.forms['translation-edit']
        form_user2[prefix + '-translation'] = u'Un tres {important} token'
        response_user2 = form_user2.submit().follow()
        self.assertEqual(response_user2.status_code, 200)

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

    def test_success_to_change_one_translation_field(self):
        self.create_poentry(u'An {important} token', u'Un token {important}.')

        response = self.app.get(self.url, user=self.admin_user)
        form = response.forms['translation-edit']

        prefix1 = get_field_prefix(form, 'msgid', 'An {important} token')
        form[prefix1 + '-translation'] = 'Un token tres {important}.'

        response = form.submit().follow()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li class="success">Changed 1 translations</li>')

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

    def test_search_on_msgid(self):
        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        form = response.forms['translation-search']
        form['search_tags'] = "comment"  # search should be case-insensitive

        response = form.submit()
        self.assertContains(response, "String 3 with comment")  # The message ID searched for

    def test_search_on_msgstr(self):
        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        form = response.forms['translation-search']
        form['search_tags'] = "translation"  # search should be case-insensitive

        response = form.submit()
        self.assertContains(response, "String 2")  # The message ID associated with the context result
        self.assertContains(response, "Translation of string 2")  # The message string we searched for

    def test_search_on_context(self):
        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        form = response.forms['translation-search']
        form['search_tags'] = "context"  # search should be case-insensitive

        response = form.submit()
        self.assertContains(response, "Context hint")  # The context hint we searched for
        self.assertContains(response, "String 4")  # The message string associated with the context result

    def test_single_edit_filter_on_type(self):
        """
        Go to the file detail view, make an edit to a translation, and submit.
        Check that this translation has changed in the PO file.
        """
        response = self.app.get('{}?type=untranslated'.format(self.url), user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        # First string: u'String 1' -> u''
        msgid_to_edit = translation_edit_form['form-0-msgid'].value
        msghash_to_edit = get_hash_from_msgid_context(msgid_to_edit, '')
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
        self.assertEqual(only_file_edit.msghash, msghash_to_edit)
        self.assertEqual(only_file_edit.new_value, new_translation)

    def test_start_with_new_line_not_edited(self):
        self.create_poentry(u'\nWith enter', u'\nWith enters')

        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        # First string: u'String 1' -> u''
        msgid_to_edit = translation_edit_form['form-5-msgid'].value
        msghash_to_edit = get_hash_from_msgid_context(msgid_to_edit, '')
        self.assertEqual(translation_edit_form['form-5-translation'].value, u'\nWith enters')

        new_translation = u'met enters'
        translation_edit_form['form-5-translation'] = new_translation
        response = translation_edit_form.submit().follow()
        self.assertEqual(response.status_code, 200)

        # Check the file
        pofile = self.transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_to_edit).msgstr, "\n{}".format(new_translation))

        # Check the edit history
        file_edits = self.transfile.edit_logs.all()
        self.assertEqual(file_edits.count(), 1)

        only_file_edit = file_edits.first()
        self.assertEqual(only_file_edit.msghash, msghash_to_edit)
        self.assertEqual(only_file_edit.new_value, new_translation)

    def test_end_with_new_line_not_edited(self):
        self.create_poentry(u'with enter\n', u'with enters\n')

        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        # First string: u'String 1' -> u''
        msgid_to_edit = translation_edit_form['form-5-msgid'].value
        msghash_to_edit = get_hash_from_msgid_context(msgid_to_edit, '')
        self.assertEqual(translation_edit_form['form-5-translation'].value, u'with enters\n')

        new_translation = u'met enters'
        translation_edit_form['form-5-translation'] = new_translation
        response = translation_edit_form.submit().follow()
        self.assertEqual(response.status_code, 200)

        # Check the file
        pofile = self.transfile.get_polib_object()
        self.assertEqual(pofile.find(msgid_to_edit).msgstr, "{}\n".format(new_translation))

        # Check the edit history
        file_edits = self.transfile.edit_logs.all()
        self.assertEqual(file_edits.count(), 1)

        only_file_edit = file_edits.first()
        self.assertEqual(only_file_edit.msghash, msghash_to_edit)
        self.assertEqual(only_file_edit.new_value, new_translation)

    def test_leading_trailing_whitespace(self):
        """
        Assert that leading/trailing whitespace doesn't reject the changes.

        Regression caused by leading whitespace in the extracted message,
        which is stripped off in the form cleaning [built in in Django, enabled
        by default].
        """
        self.create_poentry(u'plain string', u' plain string ')

        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        translation_edit_form = response.forms['translation-edit']

        # 5th entry is ours
        self.assertEqual(
            translation_edit_form['form-5-translation'].value,
            u' plain string '
        )

        translation_edit_form['form-5-translation'] = u'new translation'
        response = translation_edit_form.submit().follow()
        self.assertEqual(response.status_code, 200)

        # Check the file
        pofile = self.transfile.get_polib_object()
        self.assertEqual(
            pofile.find('plain string').msgstr,
            u'new translation'
        )


class FileListViewTests(POFileTestCase, WebTest):

    test_pofile_name = 'statstest.po.example'

    def setUp(self):
        super(FileListViewTests, self).setUp()

        self.admin_user = AdminFactory.create()
        self.user = UserFactory.create()
        self.url = reverse('mobetta:file_list', kwargs={'lang_code': 'nl'})

    def test_login_required(self):
        self.app.get(self.url, status=302)

    def test_no_permission(self):
        self.app.get(self.url, user=self.user, status=403)

    def test_file_stats(self):

        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

        soup = response.html
        file_row = soup.find('tr', id="file_detail_{}".format(self.transfile.pk))

        col_titles = ['appname', 'percent_translated', 'total_messages',
                      'translated', 'fuzzy', 'obsolete', 'filename', 'created']

        stats_cells = file_row.find_all('td', recursive=False)
        stats_results = dict(zip(col_titles, [cell.text for cell in list(stats_cells)]))

        self.assertEqual(Decimal(stats_results['percent_translated']), Decimal(25.0))
        self.assertEqual(int(stats_results['total_messages']), 4)
        self.assertEqual(int(stats_results['translated']), 1)
        self.assertEqual(int(stats_results['fuzzy']), 0)
        self.assertEqual(int(stats_results['obsolete']), 0)
        self.assertEqual(stats_results['filename'], self.pofile_path)


def get_column(response, column_name):
    """
    Return a list of BeautifulSoup <td> Tag for a given column name.
    """
    # Tricky way of getting the number of the expected column in the table.
    col_number = next(
        (i for i, tag in enumerate(response.html.thead.tr.find_all('th')) if column_name in str(tag)),
        None
    )

    lines = response.html.tbody.find_all('tr')

    return [line.find_all('td')[col_number] for line in lines]


class EditHistoryViewTests(POFileTestCase, WebTest):

    def setUp(self):
        super(EditHistoryViewTests, self).setUp()

        self.admin_user = AdminFactory.create()
        self.url = reverse('mobetta:edit_history', args=(self.transfile.pk,))

    def test_get_access_if_authenticated(self):
        response = self.app.get(self.url, user=self.admin_user)
        self.assertEqual(response.status_code, 200)

    def test_get_redirect_to_login_page_if_not_authenticated(self):
        response = self.app.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login/?next=' + self.url, response['Location'])

    def test_can_order_by_time_asc(self):
        logs = EditLogFactory.create_batch(3, file_edited=self.transfile)

        logs[0].created, logs[1].created, logs[2].created = (
            datetime(2016, 8, 1), datetime(2016, 8, 2), datetime(2016, 8, 3)
        )

        logs[0].save()
        logs[1].save()
        logs[2].save()
        response = self.app.get(
            self.url + '?order_by=time',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'time')

        self.assertIn('Aug. 1, 2016', values[0].contents[0])
        self.assertIn('Aug. 2, 2016', values[1].contents[0])
        self.assertIn('Aug. 3, 2016', values[2].contents[0])

    def test_can_order_by_time_desc(self):
        logs = EditLogFactory.create_batch(3, file_edited=self.transfile)

        logs[0].created, logs[1].created, logs[2].created = (
            datetime(2016, 8, 1), datetime(2016, 8, 2), datetime(2016, 8, 3)
        )

        logs[0].save()
        logs[1].save()
        logs[2].save()
        response = self.app.get(
            self.url + '?order_by=-time',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'time')

        self.assertIn('Aug. 3, 2016', values[0].contents[0])
        self.assertIn('Aug. 2, 2016', values[1].contents[0])
        self.assertIn('Aug. 1, 2016', values[2].contents[0])

    def test_can_order_by_user_asc(self):
        user1 = UserFactory.create(username='Adam')
        user2 = UserFactory.create(username='Barney')
        user3 = UserFactory.create(username='Cersei')

        EditLogFactory.create(user=user1, file_edited=self.transfile)
        EditLogFactory.create(user=user2, file_edited=self.transfile)
        EditLogFactory.create(user=user3, file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=user',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'user')

        self.assertIn('Adam', values[0].contents[0])
        self.assertIn('Barney', values[1].contents[0])
        self.assertIn('Cersei', values[2].contents[0])

    def test_can_order_by_user_desc(self):
        user1 = UserFactory.create(username='Adam')
        user2 = UserFactory.create(username='Barney')
        user3 = UserFactory.create(username='Cersei')

        EditLogFactory.create(user=user1, file_edited=self.transfile)
        EditLogFactory.create(user=user2, file_edited=self.transfile)
        EditLogFactory.create(user=user3, file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=-user',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'user')

        self.assertIn('Cersei', values[0].contents[0])
        self.assertIn('Barney', values[1].contents[0])
        self.assertIn('Adam', values[2].contents[0])

    def test_can_order_by_msgid_asc(self):
        EditLogFactory.create(msgid='Awesome', file_edited=self.transfile)
        EditLogFactory.create(msgid='Boring', file_edited=self.transfile)
        EditLogFactory.create(msgid='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=msgid',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'msgid')

        self.assertIn('Awesome', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Crazy', values[2].contents[0])

    def test_can_order_by_msgid_desc(self):
        EditLogFactory.create(msgid='Awesome', file_edited=self.transfile)
        EditLogFactory.create(msgid='Boring', file_edited=self.transfile)
        EditLogFactory.create(msgid='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=-msgid',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'msgid')

        self.assertIn('Crazy', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Awesome', values[2].contents[0])

    def test_can_order_by_field_name_asc(self):
        EditLogFactory.create(fieldname='Awesome', file_edited=self.transfile)
        EditLogFactory.create(fieldname='Boring', file_edited=self.transfile)
        EditLogFactory.create(fieldname='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=fieldname',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'fieldname')

        self.assertIn('Awesome', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Crazy', values[2].contents[0])

    def test_can_order_by_field_name_desc(self):
        EditLogFactory.create(fieldname='Awesome', file_edited=self.transfile)
        EditLogFactory.create(fieldname='Boring', file_edited=self.transfile)
        EditLogFactory.create(fieldname='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=-fieldname',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'fieldname')

        self.assertIn('Crazy', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Awesome', values[2].contents[0])

    def test_can_order_by_old_value_asc(self):
        EditLogFactory.create(old_value='Awesome', file_edited=self.transfile)
        EditLogFactory.create(old_value='Boring', file_edited=self.transfile)
        EditLogFactory.create(old_value='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=old_value',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'old_value')

        self.assertIn('Awesome', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Crazy', values[2].contents[0])

    def test_can_order_by_old_value_desc(self):
        EditLogFactory.create(old_value='Awesome', file_edited=self.transfile)
        EditLogFactory.create(old_value='Boring', file_edited=self.transfile)
        EditLogFactory.create(old_value='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=-old_value',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'old_value')

        self.assertIn('Crazy', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Awesome', values[2].contents[0])

    def test_can_order_by_new_value_asc(self):
        EditLogFactory.create(new_value='Awesome', file_edited=self.transfile)
        EditLogFactory.create(new_value='Boring', file_edited=self.transfile)
        EditLogFactory.create(new_value='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=new_value',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'new_value')

        self.assertIn('Awesome', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Crazy', values[2].contents[0])

    def test_can_order_by_new_value_desc(self):
        EditLogFactory.create(new_value='Awesome', file_edited=self.transfile)
        EditLogFactory.create(new_value='Boring', file_edited=self.transfile)
        EditLogFactory.create(new_value='Crazy', file_edited=self.transfile)

        response = self.app.get(
            self.url + '?order_by=-new_value',
            user=self.admin_user
        )
        self.assertEqual(response.status_code, 200)

        values = get_column(response, 'new_value')

        self.assertIn('Crazy', values[0].contents[0])
        self.assertIn('Boring', values[1].contents[0])
        self.assertIn('Awesome', values[2].contents[0])


class DownloadPOFileViewTests(POFileTestCase, WebTest):

    def setUp(self):
        super(DownloadPOFileViewTests, self).setUp()

        self.admin_user = AdminFactory.create()

    def test_fail_if_targeted_translation_file_does_not_exist(self):
        """
        response = self.app.get(
            reverse('mobetta:download', args=(666,)),
            user=self.admin_user,
        )

        self.assertEqual(response.status_code, 404)
        """

    def test_succeed_to_download_po_file(self):
        pass


class TranslationAccessTests(MultiplePOFilesTestCase, WebTest):

    test_pofiles = [
        ('django.po.example', 'es'),
        ('django.po.example', 'nl'),
        ('django.po.example', 'cy'),
    ]

    def setUp(self):
        super(TranslationAccessTests, self).setUp()

        self.normal_user = UserFactory.create()
        self.admin_user = AdminFactory.create()

        self.spanish_file = TranslationFile.objects.get(language_code='es')
        self.dutch_file = TranslationFile.objects.get(language_code='nl')
        self.welsh_file = TranslationFile.objects.get(language_code='cy')

    def test_unauthorised_access(self):
        url = reverse('mobetta:file_detail', args=(self.spanish_file.pk,))
        response = self.app.get(url, user=self.normal_user, status=403)

        self.assertEqual(response.status_code, 403)

    def test_grant_language_access(self):
        """
        First add normal_user to the translation group (as the admin)
        then test if they can edit a translation on that file.
        (And none of the others)
        """
        url = reverse('mobetta:add_translator')
        response = self.app.get(url, user=self.admin_user)

        self.assertEqual(response.status_code, 200)

        form = response.forms['add-translator-form']
        form['user'] = self.normal_user.pk
        form['language'] = 'cy'

        response = form.submit().follow()

        self.assertIn(_("{user} successfully added as a translator for {language}").format(
            user=str(self.normal_user).capitalize(),
            language=dict(settings.LANGUAGES)['cy']
        ), response.text)

        # Now try to access the Welsh translation file list as a normal user
        url = reverse('mobetta:file_list', kwargs={'lang_code': 'cy'})
        response = self.app.get(url, user=self.normal_user)
        self.assertEqual(response.status_code, 200)

        # Now go to the file detail itself and change a translation
        welsh_file = TranslationFile.objects.get(language_code='cy')
        url = reverse('mobetta:file_detail', args=(welsh_file.pk,))
        response = self.app.get(url, user=self.normal_user)
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
        pofile = welsh_file.get_polib_object()
        self.assertEqual(pofile.find(msgid_to_edit).msgstr, new_translation)

        # Now try editing a file they're not allowed to edit
        spanish_file = TranslationFile.objects.get(language_code='es')
        url = reverse('mobetta:file_detail', args=(spanish_file.pk,))
        response = self.app.get(url, user=self.normal_user, status=403)
        self.assertEqual(response.status_code, 403)

        # ..and make sure only the correct languages show up in the language list
        url = reverse('mobetta:language_list')
        response = self.app.get(url, user=self.normal_user)
        self.assertIn(_('Welsh'), response.text)
        self.assertNotIn(_('Spanish'), response.text)
