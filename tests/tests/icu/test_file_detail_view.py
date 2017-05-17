# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

import pytest

from ..factories import AdminFactory, UserFactory


@pytest.mark.django_db
def test_login_required(django_app, icu_file):
    django_app.get(
        reverse('mobetta:icu_file_detail', args=(icu_file.pk,)),
        status=302
    )


@pytest.mark.django_db
def test_no_permission(django_app, icu_file):
    user = UserFactory.create()
    django_app.get(
        reverse('mobetta:icu_file_detail', args=(icu_file.pk,)),
        user=user, status=403
    )


@pytest.mark.django_db
def test_single_edit(django_app, real_icu_file):
    user = AdminFactory.create()
    url = reverse('mobetta:icu_file_detail', kwargs={'pk': real_icu_file.pk})
    response = django_app.get(url, user=user)
    assert response.status_code == 200

    translation_edit_form = response.forms['translation-edit']
    assert translation_edit_form['form-0-msgid'].value == 'some.key1'
    assert translation_edit_form['form-0-translation'].value == 'some.translation1'
    assert translation_edit_form['form-1-msgid'].value == 'some.key2'
    assert translation_edit_form['form-1-translation'].value == 'some.translation2'

    # set a translation
    translation_edit_form['form-0-translation'] = 'Translatèd string'
    response = translation_edit_form.submit().follow()
    assert response.status_code == 200

    # check that the file was effectively updated
    icu_file = real_icu_file.get_icufile_object()
    assert icu_file.contents['some.key1'] == 'Translatèd string'

    # Check the edit history
    file_edits = real_icu_file.edit_logs.all()
    assert file_edits.count() == 1
    only_file_edit = file_edits.first()
    assert only_file_edit.msghash == 'some.key1'
    assert only_file_edit.new_value == 'Translatèd string'


@pytest.mark.django_db
def test_submit_with_no_changes(django_app, real_icu_file):
    user = AdminFactory.create()
    url = reverse('mobetta:icu_file_detail', kwargs={'pk': real_icu_file.pk})
    response = django_app.get(url, user=user)
    assert response.status_code == 200
    form = response.forms['translation-edit']
    form['form-0-translation'] = 'some.translation1'

    response = form.submit().follow()
    assert response.status_code == 200

    # check that the file is unchanged
    file_edits = real_icu_file.edit_logs.all()
    assert file_edits.count() == 0


@pytest.mark.django_db
def test_simultaneous_edits_blocked(django_app, real_icu_file):
    """
    Go to the file detail view as two different users. Make an edit as one of the
    users and submit, then make an edit as the other user and submit.
    The second user's edit should be blocked, and the old_translation field should
    reflect the result of the first user's edit.
    """
    url = reverse('mobetta:icu_file_detail', kwargs={'pk': real_icu_file.pk})
    first_user = AdminFactory.create()
    second_user = AdminFactory.create()

    first_user_response = django_app.get(url, user=first_user)
    assert first_user_response.status_code == 200
    second_user_response = django_app.get(url, user=second_user)
    assert second_user_response.status_code == 200

    # Make the edit as the first user
    first_user_edit_form = first_user_response.forms['translation-edit']
    first_user_edit_form['form-0-translation'] = 'First user translation'
    first_user_response = first_user_edit_form.submit().follow()
    assert first_user_response.status_code == 200

    # Try to make a similar edit as the second user
    second_user_edit_form = second_user_response.forms['translation-edit']
    assert second_user_edit_form['form-0-msgid'].value == 'some.key1'
    assert second_user_edit_form['form-0-translation'].value == 'some.translation1'

    second_user_edit_form['form-0-translation'] = "Second user translation"
    second_user_response = second_user_edit_form.submit()

    expected_err_msg = _("This value was edited while you were editing it "
                         "(new value: %s)") % 'First user translation'
    assert expected_err_msg in second_user_response.text

    # The old_translation in the form should now reflect the first user's translation
    second_user_edit_form = second_user_response.forms['translation-edit']
    assert second_user_edit_form['form-0-old_translation'].value == 'First user translation'

    # verify file contents
    icu_file = real_icu_file.get_icufile_object()
    assert icu_file.contents['some.key1'] == 'First user translation'

    # Check the edit history: the rejected edit shouldn't be in there
    file_edits = real_icu_file.edit_logs.all()
    assert file_edits.count() == 1


@pytest.mark.django_db
def test_message_format_validated(django_app, real_icu_file):
    """
    Assert that submitted translations syntax is validated.
    """
    url = reverse('mobetta:icu_file_detail', kwargs={'pk': real_icu_file.pk})
    user = AdminFactory.create()
    response = django_app.get(url, user=user)
    form = response.forms['translation-edit']
    form['form-0-translation'] = 'Unclosed brace {'  # invalid syntax
    response = form.submit()
    assert response.status_code == 200
    assert response.context['formset'].errors == [
        {'translation': [_('Invalid message syntax')]},
        {}
    ]


@pytest.mark.django_db
def test_filter_translations_by_tag(django_app, real_icu_file):
    """
    Assert that messages can be filtered by searching on key/translation.
    """
    user = AdminFactory.create()
    url = reverse('mobetta:icu_file_detail', kwargs={'pk': real_icu_file.pk})
    response = django_app.get(url, user=user)
    assert response.status_code == 200

    search_form = response.forms['translation-search']
    search_form['search_tags'] = 'some.key1'

    response = search_form.submit()
    assert response.status_code == 200
    search_form = response.forms['translation-search']
    assert search_form['search_tags'].value == 'some.key1'

    form = response.forms['translation-edit']
    assert form['form-0-msgid'].value == 'some.key1'
    assert form['form-0-translation'].value == 'some.translation1'
    assert 'form-1-msgid' not in form.fields
    assert 'form-1-translation' not in form.fields


@pytest.mark.django_db
def test_search_regex(django_app, real_icu_file):
    user = AdminFactory.create()
    url = reverse('mobetta:icu_file_detail', kwargs={'pk': real_icu_file.pk})
    response = django_app.get(url, user=user)
    assert response.status_code == 200

    search_form = response.forms['translation-search']
    search_form['search_tags'] = 'some.key\d+'

    response = search_form.submit()
    assert response.status_code == 200
    search_form = response.forms['translation-search']
    assert search_form['search_tags'].value == 'some.key\d+'

    form = response.forms['translation-edit']
    assert form['form-0-msgid'].value == 'some.key1'
    assert form['form-0-translation'].value == 'some.translation1'
    assert form['form-1-msgid'].value == 'some.key2'
    assert form['form-1-translation'].value == 'some.translation2'


@pytest.mark.django_db
def test_search_invalid_regex(django_app, real_icu_file):
    user = AdminFactory.create()
    url = reverse('mobetta:icu_file_detail', kwargs={'pk': real_icu_file.pk})
    response = django_app.get(url, user=user)
    assert response.status_code == 200

    search_form = response.forms['translation-search']
    search_form['search_tags'] = 'some.key('
    response = search_form.submit()
    assert response.status_code == 200

    form = response.forms['translation-edit']
    assert 'form-0-msgid' not in form.fields
    assert 'form-0-translation' not in form.fields
    assert 'form-1-msgid' not in form.fields
    assert 'form-1-translation' not in form.fields
