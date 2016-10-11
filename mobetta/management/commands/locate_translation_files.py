from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from mobetta.models import TranslationFile
from mobetta.util import find_pofiles, app_name_from_filepath


class Command(BaseCommand):
    help = ("Send SMS notifications to workers for tomorrow's assignments")

    def add_arguments(self, parser):
         parser.add_argument('--include-third-party',
            action='store_true',
            help='Detect translation files for third-party apps',
            dest='include_third_party',
            default=False)

    def handle(self, *args, **options):
        """
        Find all translation files and populate the database with them.
        """

        for lang_code, lang_name in settings.LANGUAGES:
            filepaths = find_pofiles(lang_code, third_party_apps=options.get('include_third_party'))
            if len(filepaths) > 0:
                print("{} filepaths found for language {}".format(len(filepaths), lang_name))

            for fp in filepaths:
                obj, created = TranslationFile.objects.get_or_create(
                    name=app_name_from_filepath(fp),
                    filepath=fp,
                    language_code=lang_code
                )
                print("{} Created: {}".format(fp, created))
