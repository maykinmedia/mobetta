from django.conf import settings
from django.core.management import BaseCommand

from mobetta.models import TranslationFile
from mobetta.util import app_name_from_filepath, find_pofiles


class Command(BaseCommand):
    help = "Scan the project directory and locate translation files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--include-third-party', action='store_true',
            help='Detect translation files for third-party apps',
        )

    def handle(self, **options):
        """
        Find all translation files and populate the database with them.
        """

        for lang_code, lang_name in settings.LANGUAGES:
            filepaths = find_pofiles(lang_code, third_party_apps=options['include_third_party'])
            if len(filepaths) > 0:
                print("{} filepaths found for language {}".format(len(filepaths), lang_name))

            for fp in filepaths:
                obj, created = TranslationFile.objects.get_or_create(
                    name=app_name_from_filepath(fp),
                    filepath=fp,
                    language_code=lang_code
                )
                self.stdout.write("{} Created: {}".format(fp, created))
