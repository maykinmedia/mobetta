from __future__ import absolute_import, unicode_literals

import os

from django.core.exceptions import ValidationError


def validate_filepath_exists(value):
    if not os.path.exists(value):
        raise ValidationError("Invalid filepath", code='invalid')
