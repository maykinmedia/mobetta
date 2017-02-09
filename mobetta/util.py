"""
Copyright (c) 2008-2010 Marco Bonetti

 Permission is hereby granted, free of charge, to any person
 obtaining a copy of this software and associated documentation
 files (the "Software"), to deal in the Software without
 restriction, including without limitation the rights to use,
 copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following
 conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.
"""
import datetime
import hashlib
import os
import unicodedata

import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import six, timezone

from .conf.settings import MOBETTA_PO_FILENAMES


def fix_newlines(inval, outval):
    """
    Fixes submitted translations by filtering carriage returns and pairing
    newlines at the begging and end of the translated string with the original
    """
    if 0 == len(inval) or 0 == len(outval):
        return outval

    if "\r" in outval and "\r" not in inval:
        outval = outval.replace("\r", '')

    if "\n" == inval[0] and "\n" != outval[0]:
        outval = "\n" + outval
    elif "\n" != inval[0] and "\n" == outval[0]:
        outval = outval.lstrip()
    if "\n" == inval[-1] and "\n" != outval[-1]:
        outval = outval + "\n"
    elif "\n" != inval[-1] and "\n" == outval[-1]:
        outval = outval.rstrip()
    return outval


def get_token_regexes():
    return [
        r'(?:\{[^\}\n]*\})',  # Python3 format tokens
        r'(?:%\([^\)]*\)[acdefgiorsux])',  # Python2 format tokens
        r'(?:\{{2}[^\}\n]*\}{2})',  # Django template variables
    ]


def get_version():
    """
    TODO: Probably use a config file for this.
    """
    return u"0.0.2"


def message_is_fuzzy(message):
    return message and hasattr(message, 'flags') and 'fuzzy' in message.flags


def get_occurrences(poentry):
    subset = [source + ':' + line for source, line in poentry.occurrences[:2]]

    size = len(poentry.occurrences)
    if size > 2:
        subset.append('... and {} more !'.format(size - 2))

    return '<br />'.join(subset)


def app_name_from_filepath(path):
    app = path.split("/locale")[0].split("/")[-1]
    return app


def timestamp_for_metadata(dt=None):
    """
    Return a timestamp with a timezone for the configured locale.  If all else
    fails, consider localtime to be UTC.

    Originally written by Marco Bonetti.
    """
    dt = dt or datetime.datetime.now()
    if timezone is None:
        return dt.strftime('%Y-%m-%d %H:%M%z')
    if not dt.tzinfo:
        tz = timezone.get_current_timezone()
        if not tz:
            tz = timezone.utc
        dt = dt.replace(tzinfo=timezone.get_current_timezone())
    return dt.strftime("%Y-%m-%d %H:%M%z")


def update_metadata(pofile, first_name=None, last_name=None, email=None):
    pofile.metadata['Last-Translator'] = unicodedata.normalize('NFKD', u"%s %s <%s>" % (
        first_name or u'Anonymous',
        last_name or u'User',
        email or u'anonymous@user.tld'
    ))

    pofile.metadata['X-Translated-Using'] = u"Mobetta %s" % get_version()
    pofile.metadata['PO-Revision-Date'] = timestamp_for_metadata()


def update_translations(pofile, form_changes):
    """
    Takes in a ``POFile`` (from `polib`) and a list of changes, and applies these changes
    to the PO file.
    Format of changes:
        [
            (<form>, [
                {
                'msgid': <msgid>,
                'field': '<field_name>',
                'from': '<old_value>',
                'to': '<new_value>',
                },
                ...
            ]),
            ...
        ]
    """
    applied_changes = []
    rejected_changes = []

    for form, changes in form_changes:
        for change in changes:
            entry = None

            for poentry in pofile:
                if get_message_hash(poentry) == change['md5hash']:
                    entry = poentry
                    break

            if entry:
                # Check that the 'from' attr is the same as the current content
                if change['field'] == 'translation':
                    if entry.msgstr == change['from'] or entry.msgstr.replace('\n', '') == change['from'].replace('\r',''):
                        entry.msgstr = fix_newlines(entry.msgid, change['to'])
                        applied_changes.append((form, change))
                    else:
                        change.update({
                            'po_value': entry.msgstr
                        })
                        rejected_changes.append((form, change))

                elif change['field'] == 'fuzzy':
                    # No need to check for simultaneous edits of 'fuzzy'
                    # since there are only two possible values.
                    if change['to'] and 'fuzzy' not in entry.flags:
                        entry.flags.append('fuzzy')
                    elif not change['to'] and 'fuzzy' in entry.flags:
                        entry.flags.remove('fuzzy')
                    applied_changes.append((form, change))

                elif change['field'] == 'context':
                    if entry.msgctxt is None or entry.msgctxt == change['from']:
                        entry.msgctxt = change['to']
                        applied_changes.append((form, change))
                    else:
                        change.update({
                            'po_value': entry.msgctxt
                        })
                        rejected_changes.append((form, change))
            else:
                raise RuntimeError("Entry not found!")

    return applied_changes, rejected_changes


def find_pofiles(lang, project_apps=True, third_party_apps=False):
    """
    Scans app directories for gettext catalogues for the given language.

    Originally written by Marco Bonetti.
    """
    from django.apps import apps

    paths = []

    if not hasattr(settings, 'BASE_DIR'):
        raise ImproperlyConfigured(
            "mobetta needs the `BASE_DIR` setting, "
            "which should hold the absolute path to the project root.")

    # custom paths specified in settings
    for localepath in settings.LOCALE_PATHS:
        if os.path.isdir(localepath):
            paths.append(localepath)

    # project/app/locale
    abs_project_path = os.path.realpath(settings.BASE_DIR) + os.path.sep
    django_dir = os.path.realpath(os.path.abspath(os.path.dirname(django.__file__))) + os.path.sep
    for app_config in apps.get_app_configs():
        app_dir = os.path.realpath(app_config.path) + os.path.sep

        # ignore django apps - django ships its .mo files and an update would overwrite them
        if app_dir.startswith(django_dir):
            continue

        # ignore third party packages?
        # NOTE: if a third party package ships with the .mo file(s), these will also get
        # overwritten on updates...
        if not third_party_apps and not app_dir.startswith(abs_project_path):
            continue

        # ignore project apps?
        if not project_apps and app_dir.startswith(abs_project_path):
            continue

        # TODO: Handle excluded apps in project or mobetta settings
        ldir = os.path.join(app_dir, 'locale')
        if os.path.isdir(ldir):
            paths.append(ldir)

    # ensure all locale combinations are detected, e.g. nl_nl, nl_NL, nl-nl and
    # nl-NL
    langs = [lang]
    for splitter in ['-', '_']:
        if splitter in lang:
            lang_code, country_code = lang.lower().split(splitter)
            langs += [
                "%s%s%s" % (lang_code, splitter, country_code),
                "%s%s%s" % (lang_code, splitter, country_code.upper())
            ]

    # normalize paths and remove duplicates
    paths = {os.path.normpath(path) for path in paths}
    abspaths = set()
    for path in paths:
        # TODO: blakclist paths?
        for lang_ in langs:
            dirname = os.path.join(path, lang_, 'LC_MESSAGES')
            for name in MOBETTA_PO_FILENAMES:
                filename = os.path.join(dirname, name)
                if os.path.isfile(filename):
                    abspaths.add((filename))

    return list(sorted(abspaths))


def get_translator():
    import microsofttranslator
    return microsofttranslator.Translator(settings.MS_TRANSLATE_CLIENT_ID, settings.MS_TRANSLATE_CLIENT_SECRET)


def get_automated_translation(translator, original_string, language_code):
    return translator.translate(original_string, language_code)


def get_automated_translations(translator, strings_to_translate, language_code):
    result = translator.translate_array(strings_to_translate, language_code)
    return dict(zip(strings_to_translate, [t['TranslatedText'] for t in result]))


def get_hash_from_msgid_context(msgid, msgctxt):
    return hashlib.md5(
        (six.text_type(msgid) +
            six.text_type(msgctxt or "")).encode('utf8')
    ).hexdigest()


def get_message_hash(entry):
    return get_hash_from_msgid_context(entry.msgid, entry.msgctxt)
