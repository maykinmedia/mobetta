import json
from collections import OrderedDict

from django.apps import apps

import pytest

if apps.is_installed('mobetta.icu'):
    from .factories import ICUTranslationFileFactory

    @pytest.fixture
    def icu_file(db):
        return ICUTranslationFileFactory.create()

    @pytest.fixture
    def real_icu_file(db, tmpdir):
        messages = OrderedDict((
            ('some.key1', 'some.translation1'),
            ('some.key2', 'some.translation2'),
        ))
        outfile = tmpdir.join('nl.json')
        with outfile.open('w') as _outfile:
            json.dump(messages, _outfile)
        return ICUTranslationFileFactory.create(filepath=str(outfile), language_code='en')
