from django import template

from ..models import EditLog, MessageComment

register = template.Library()


@register.inclusion_tag('mobetta/include/_last_msg_edit.html')
def last_edit(transfile, msghash):
    """
    Return the last EditLog instance for this msghash for this file.

    ``transfile`` - the `TranslationFile` object to get the log for.
    ``msghash`` - the md5 hash of the msgid and msgctxt to find the log for.
    """
    try:
        logentry = EditLog.objects.filter(
            file_edited=transfile,
            msghash=msghash
        ).order_by('-created').first()
    except EditLog.DoesNotExist:
        logentry = None

    return {
        'logentry': logentry
    }


@register.simple_tag
def comment_count(transfile, msghash):
    return MessageComment.objects.filter(
        translation_file=transfile,
        msghash=msghash
    ).count()


@register.filter
def get_item(dictionary, key):
    """
    Return the value at dictionary[key].
    For some reason this isn't allowed directly in Django templates.
    """
    return dictionary.get(key)


@register.filter
def highlight_tokens(text):  # noop since this format is a *tad* bit more complicated
    return text
