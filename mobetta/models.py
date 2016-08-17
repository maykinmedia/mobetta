import polib

from django.db import models


# Create your models here.
class TranslationFile(models.Model):

    name = models.CharField(max_length=512, blank=False, null=False)
    filepath = models.CharField(max_length=1024, blank=False, null=False)
    language_code = models.CharField(max_length=32, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "{} ({})".format(self.name, self.filepath)

    @property
    def model_name(self):
        return app_name_from_filepath(self.filepath)

    def get_polib_object(self):
        return polib.pofile(self.filepath)
