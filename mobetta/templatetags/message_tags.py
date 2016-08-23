from django import template

from mobetta.models import EditLog

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

