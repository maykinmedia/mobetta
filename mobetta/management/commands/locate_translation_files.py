from django.core.management.base import BaseCommand

from mobetta.models import TranslationFile
from mobetta.util import find_pofiles, app_name_from_filepath


class Command(BaseCommand):
    help = ("Send SMS notifications to workers for tomorrow's assignments")

    def handle(self, *args, **options):
        """
        Find all translation files and populate the database with them.
        """

        language_code = 'nl'
        filepaths = find_pofiles(language_code)

        for fp in filepaths:
            TranslationFile.objects.create(
                name=app_name_from_filepath(fp),
                filepath=fp,
                language_code=language_code
            )
