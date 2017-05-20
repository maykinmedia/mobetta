import factory


class ICUTranslationFileFactory(factory.django.DjangoModelFactory):

    name = factory.Faker('word')
    language_code = 'en'

    class Meta:
        model = 'icu.ICUTranslationFile'
