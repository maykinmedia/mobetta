try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from rest_framework.test import APIClient

from mobetta.models import TranslationFile

from .utils import POFileTestCase
from .factories import AdminFactory, MessageCommentFactory, UserFactory


class APITests(POFileTestCase):

    def setUp(self):
        super(APITests, self).setUp()

        self.admin_user = AdminFactory.create()

    def test_post_comment(self):
        """
        Post a comment on one translation in the translation file.
        """
        client = APIClient()

        client.force_authenticate(user=self.admin_user)

        postdata = {
            'msgid': u"String 1",
            'translation_file': self.transfile.pk,
            'body': u"Test comment",
        }

        response = client.post(reverse('api:messagecomment-list'), postdata, format='json')

        self.assertEqual(response.status_code, 201) # 'Created'
        self.assertEqual(response.data['msgid'], u"String 1")
        self.assertEqual(response.data['translation_file'], self.transfile.pk)
        self.assertEqual(response.data['body'], u"Test comment")
        self.assertEqual(response.data['comment_count'], 1)
        self.assertEqual(response.data['user_name'], str(self.admin_user))

    def test_post_invalid_comment(self):
        """
        Post a comment with no text in the body.
        """
        client = APIClient()

        client.force_authenticate(user=self.admin_user)

        postdata = {
            'msgid': u"String 1",
            'translation_file': self.transfile.pk,
            'body': u"",
        }

        response = client.post(reverse('api:messagecomment-list'), postdata, format='json')

        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data['body'], [_('This field may not be blank.')])

    def test_post_comment_unauthorised(self):
        """
        Try to post a comment as a user without translation permissions.
        """
        client = APIClient()

        non_translator_user = UserFactory.create()

        client.force_authenticate(user=non_translator_user)

        postdata = {
            'msgid': u"String 1",
            'translation_file': self.transfile.pk,
            'body': u"",
        }

        response = client.post(reverse('api:messagecomment-list'), postdata, format='json')

        self.assertEqual(response.status_code, 403)

    def test_fetch_comments(self):
        """
        Test how we fetch comments for a particular msgid/file combination.
        """
        comment1 = MessageCommentFactory.create(
            translation_file=self.transfile,
            msgid=u"String 1",
            body=u"First comment",
        )

        comment2 = MessageCommentFactory.create(
            translation_file=self.transfile,
            msgid=u"String 1",
            body=u"Second comment",
        )

        comment3 = MessageCommentFactory.create(
            translation_file=self.transfile,
            msgid=u"String 2",
            body=u"Third comment",
        )

        comment4 = MessageCommentFactory.create(
            body=u"Other file comment"
        )

        client = APIClient()

        client.force_authenticate(user=self.admin_user)

        url = "{}?{}".format(
            reverse('api:messagecomment-list'),
            urlencode({
                'translation_file': self.transfile.pk,
                'msgid': u"String 1"
            })
        )

        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['msgid'], u"String 1")
        self.assertEqual(response.data[0]['body'], u"First comment")
        self.assertEqual(response.data[0]['translation_file'], 1)
        self.assertEqual(response.data[1]['msgid'], u"String 1")
        self.assertEqual(response.data[1]['body'], u"Second comment")
        self.assertEqual(response.data[1]['translation_file'], 1)

    def test_fetch_comments_unauthorised(self):
        """
        Make sure a non-admin user can't fetch comments.
        """
        client = APIClient()

        non_translator_user = UserFactory.create()

        client.force_authenticate(user=non_translator_user)

        url = "{}?{}".format(
            reverse('api:messagecomment-list'),
            urlencode({
                'translation_file': self.transfile.pk,
                'msgid': u"String 1"
            })
        )

        response = client.get(url, format='json')
        self.assertEqual(response.status_code, 403)
