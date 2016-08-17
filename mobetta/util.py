import os
import django
import inspect
import unicodedata
import datetime

from django.conf import settings
from django.utils import timezone


def get_version():
    """
    TODO: Probably use a config file for this.
    """
    return u"0.0.1"


def message_is_fuzzy(message):
    return message and hasattr(message, 'flags') and 'fuzzy' in message.flags


def app_name_from_filepath(path):
    app = path.split("/locale")[0].split("/")[-1]

    return app


def timestamp_for_metadata(dt=None):
    """
    Return a timestamp with a timezone for the configured locale.  If all else
    fails, consider localtime to be UTC.
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
        first_name or 'Anonymous',
        last_name or 'User',
        email or 'anonymous@user.tld'
    )).encode('ascii', 'ignore')

    pofile.metadata['X-Translated-Using'] = u"Mobetta %s" % get_version()
    pofile.metadata['PO-Revision-Date'] = timestamp_for_metadata()
    pofile.save()


def update_translations(pofile, changes):
    """
    Takes in a ``POFile`` (from `polib`) and a list of changes, and applies these changes
    to the PO file.
    Format of changes:
        [
            {
                'msgid': <msgid>,
                '<attrib_name>': '<new_value>',
                ...
            },
            ...
        ]
    """
    for change in changes:
        entry = pofile.find(change['msgid'])

        if entry:
            if 'msgstr' in change:
                old_msgstr = entry.msgstr
                entry.msgstr = change['msgstr']
            elif 'fuzzy' in change:
                old_fuzzy = 'fuzzy' in entry.flags
                if old_fuzzy and not change['fuzzy']:
                    entry.flags.remove('fuzzy')
                elif change['fuzzy'] and not old_fuzzy:
                    entry.flags.append('fuzzy')
            else:
                raise NotImplementedError()

        else:
            raise RuntimeError("Entry not found!")


def find_pofiles(lang, project_apps=True, django_apps=False, third_party_apps=False):
    """
    Scans app directories for gettext catalogues for the given language.
    """

    paths = []

    # project/locale
    parts = settings.SETTINGS_MODULE.split('.')
    project = __import__(parts[0], {}, {}, [])
    abs_project_path = os.path.normpath(os.path.abspath(os.path.dirname(project.__file__)))

    if project_apps:
        internal_path = os.path.abspath(os.path.join(os.path.dirname(project.__file__), 'locale'))
        if os.path.exists(internal_path):
            paths.append(internal_path)

        external_path = os.path.abspath(os.path.join(os.path.dirname(project.__file__), '..', 'locale'))
        if os.path.exists(external_path):
            paths.append(external_path)

    # django/locale
    if django_apps:
        django_paths = []
        for root, dirnames, filename in os.walk(os.path.abspath(os.path.dirname(django.__file__))):
            if 'locale' in dirnames:
                django_paths.append(os.path.join(root, 'locale'))
                continue

        paths = paths + django_paths

    # custom paths specified in settings
    for localepath in settings.LOCALE_PATHS:
        if os.path.isdir(localepath):
            paths.append(localepath)

    # project/app/locale
    has_appconfig = False
    for appname in settings.INSTALLED_APPS:
        # TODO: Handle excluded apps in project or mobetta settings
        p = appname.rfind('.')
        if p >= 0:
            app = getattr(__import__(appname[:p], {}, {}, [str(appname[p + 1:])]), appname[p + 1:])
        else:
            app = __import__(appname, {}, {}, [])

        # Convert AppConfig (Django 1.7+) to application module
        if django.VERSION[0:2] >= (1, 7):
            if inspect.isclass(app) and issubclass(app, AppConfig):
                has_appconfig = True
                continue

        app_path = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(app.__file__), 'locale')))

        # ignore 'contrib' apps if we're ignoring Django apps
        if not django_apps and 'contrib' in app_path and 'django' in app_path:
            continue

        # third party external
        if not third_party_apps and abs_project_path not in app_path:
            continue

        # local apps
        if not project_apps and abs_project_path in app_path:
            continue

        if os.path.isdir(app_path):
            paths.append(app_path)

    # Handling using AppConfigs is messy, but we can just get the app paths directly
    # from the apps object
    if has_appconfig:
        for app_ in apps.get_app_configs():
            # TODO: Handle excluded apps in project or mobetta settings
            app_path = app_.path

            # maybe ignore django apps
            if not django_apps and 'contrib' in app_path and 'django' in app_path:
                continue

            # maybe ignore third party external
            if not third_party_apps and abs_project_path not in app_path:
                continue

            # maybe ignore local apps
            if not project_apps and abs_project_path in app_path:
                continue

            internal_path = os.path.abspath(os.path.join(app_path, 'locale'))
            if os.path.exists(internal_path):
                paths.append(internal)
            external_path = os.path.abspath(os.path.join(app_path, '..', 'locale'))
            if os.path.exists(external_path):
                paths.append(external_path)


    # Not sure quite why this bit is here, maybe each language needs
    # two representations, like nl-NL and nl_NL.
    langs = [lang, ]
    if u'-' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'-', 1))
        langs += [u'%s_%s' % (_l, _c), u'%s_%s' % (_l, _c.upper()), ]
    elif u'_' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'_', 1))
        langs += [u'%s-%s' % (_l, _c), u'%s-%s' % (_l, _c.upper()), ]

    paths = map(os.path.normpath, paths)
    paths = list(set(paths))
    abspaths = set()

    for path in paths:
        # TODO: Exclude paths
        for lang_ in langs:
            dirname = os.path.join(path, lang_, 'LC_MESSAGES')
            # TODO: Store po_filenames in settings
            po_filenames = ['django.po', 'djangojs.po']
            for fn in po_filenames:
                filename = os.path.join(dirname, fn)
                if os.path.isfile(filename):
                    abspaths.add(os.path.abspath(filename))

    return list(sorted(abspaths))

