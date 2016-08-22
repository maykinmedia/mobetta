from factory.django import DjangoModelFactory

from django.contrib.auth.models import User


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
