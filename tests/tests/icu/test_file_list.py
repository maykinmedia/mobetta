# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.six.moves.urllib.parse import urlparse
from django.utils.translation import ugettext as _

import pytest

from ..factories import AdminFactory, UserFactory


@pytest.mark.django_db
def test_login_required(django_app):
    url = reverse('mobetta:icu_file_list', kwargs={'lang_code': 'nl'})
    response = django_app.get(url, status=302)
    redirect = urlparse(response.location)
    assert redirect.path == settings.LOGIN_URL
    assert redirect.query == 'next={}'.format(url)


@pytest.mark.django_db
def test_no_permission(django_app):
    url = reverse('mobetta:icu_file_list', kwargs={'lang_code': 'nl'})
    django_app.get(url, user=UserFactory.create(), status=403)


@pytest.mark.django_db
def test_file_stats(django_app, real_icu_file):
    user = AdminFactory.create()
    url = reverse('mobetta:icu_file_list', kwargs={'lang_code': 'nl'})
    response = django_app.get(url, user=user, status=200)
    file_row = response.html.find('tr', id='file_detail_{}'.format(real_icu_file.pk))

    col_titles = ['name', 'total_messages', 'filename',
                  'created', 'edit_history', 'download']
    stats_cells = file_row.find_all('td', recursive=False)
    stats_results = dict(zip(col_titles, [cell.text for cell in list(stats_cells)]))

    assert stats_results['name'] == real_icu_file.name
    assert stats_results['total_messages'] == '2'
    assert stats_results['filename'] == real_icu_file.filepath
    assert stats_results['edit_history'] == _('View')
    assert stats_results['download'] == _('Download')


@pytest.mark.django_db
def test_file_download_link(django_app, real_icu_file):
    """
    Assert that the download link works correctly.
    """
    user = AdminFactory.create()
    url = reverse('mobetta:icu_file_list', kwargs={'lang_code': 'nl'})
    response = django_app.get(url, user=user, status=200)
    download = response.click(_('Download'))  # there should only be one entry
    assert download.status_code == 200
    assert download.content_type == 'application/json'
    assert download.content_disposition == 'attachment; filename="{}_nl.json"'.format(
        real_icu_file.name.lower()
    )
    with open(real_icu_file.filepath, 'rb') as json_file:
        expected_content = json_file.read()
    assert download.content == expected_content
