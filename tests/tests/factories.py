from django.contrib.auth.models import User

from factory import DjangoModelFactory, SubFactory, fuzzy

from mobetta.models import EditLog, MessageComment, TranslationFile

hex_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']


class UserFactory(DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ('username', 'email', 'password')

    username = 'someruser'
    email = 'some@user.com'
    password = 'apassword'


class AdminFactory(UserFactory):

    username = 'admin'
    is_superuser = True


class TranslationFileFactory(DjangoModelFactory):
    name = 'django.po'
    filepath = 'you/shall/not/path'
    language_code = 'nl'

    class Meta:
        model = TranslationFile


class EditLogFactory(DjangoModelFactory):
    user = SubFactory(AdminFactory)
    file_edited = SubFactory(TranslationFileFactory)
    msghash = fuzzy.FuzzyText(length=32, chars=hex_chars)
    fieldname = 'default_fieldname'
    old_value = 'default_old_value'
    new_value = 'default_new_value'

    class Meta:
        model = EditLog


class MessageCommentFactory(DjangoModelFactory):
    user = SubFactory(AdminFactory)
    translation_file = SubFactory(TranslationFileFactory)
    msghash = fuzzy.FuzzyText(length=32, chars=hex_chars)
    body = 'Default message body'

    class Meta:
        model = MessageComment
