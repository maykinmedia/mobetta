import re

from django import template
from django.utils.html import escape

from mobetta.models import EditLog, MessageComment
from mobetta.util import get_token_regexes

register = template.Library()


@register.inclusion_tag('mobetta/include/_last_msg_edit.html')
def last_edit(transfile, msgid):
    """
    Return the last EditLog instance for this msgid for this file.

    ``transfile`` - the `TranslationFile` object to get the log for.
    ``msgid`` - the message ID (original message) to find the log for.
    """
    try:
        logentry = EditLog.objects.filter(
            file_edited=transfile,
            msgid=msgid
        ).order_by('-created').first()
    except EditLog.DoesNotExist:
        logentry = None

    return {
        'logentry': logentry
    }


@register.simple_tag
def comment_count(transfile, msgid):
    return MessageComment.objects.filter(
        translation_file=transfile,
        msgid=msgid
    ).count()


@register.filter
def get_item(dictionary, key):
    """
    Return the value at dictionary[key].
    For some reason this isn't allowed directly in Django templates.
    """
    return dictionary.get(key)


@register.filter
def highlight_tokens(text):
    """
    Return an HTML string with tokens highlighted in a span using the
    'token' class.
    """
    regex = '|'.join(get_token_regexes())

    text = escape(text)
    format_tokens = re.findall(regex, text)

    for t in format_tokens:
        text = text.replace(
            t,
            "<span class=\"format-token\">{}</span>".format(t)
        )

    return text
