"""
Validate that a message is a valid ICU formatted message.
"""
from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ValidationError

from icu import ICUError, MessageFormat


def validate_icu_syntax(value):
    try:
        MessageFormat(value)
    except ICUError as exc:
        error_code = exc.getErrorCode()
        error_detail = exc.messages[error_code]
        raise ValidationError(
            'Invalid message syntax',
            code='invalid', params={
                'msg': value,
                'error_code': error_code,
                'error_detail': error_detail,
            }
        )
