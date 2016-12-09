try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    from unittest import mock
except ImportError:
    import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.translation import ugettext as _

from rest_framework.test import APIClient

from mobetta.util import get_hash_from_msgid_context

from .factories import AdminFactory, MessageCommentFactory, UserFactory
from .utils import POFileTestCase


class MessageCommentAPITests(POFileTestCase):

    def setUp(self):
        super(MessageCommentAPITests, self).setUp()

        self.admin_user = AdminFactory.create()

    def test_post_comment(self):
        """
        Post a comment on one translation in the translation file.
        """
        client = APIClient()

        client.force_authenticate(user=self.admin_user)

        msgid = u"String 1"
        msghash = get_hash_from_msgid_context(msgid, '')

        postdata = {
            'msghash': msghash,
            'translation_file': self.transfile.pk,
            'body': u"Test comment",
        }

        response = client.post(reverse('mobetta:api:messagecomment-list'), postdata, format='json')

        self.assertEqual(response.status_code, 201)  # 'Created'
        self.assertEqual(response.data['msghash'], msghash)
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

        msgid = u"String 1"
        msghash = get_hash_from_msgid_context(msgid, '')

        postdata = {
            'msghash': msghash,
            'translation_file': self.transfile.pk,
            'body': u"",
        }

        response = client.post(reverse('mobetta:api:messagecomment-list'), postdata, format='json')

        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.data['body'], [_('This field may not be blank.')])

    def test_post_comment_unauthorised(self):
        """
        Try to post a comment as a user without translation permissions.
        """
        client = APIClient()

        non_translator_user = UserFactory.create()

        client.force_authenticate(user=non_translator_user)

        msgid = u"String 1"
        msghash = get_hash_from_msgid_context(msgid, '')

        postdata = {
            'msghash': msghash,
            'translation_file': self.transfile.pk,
            'body': u"",
        }

        response = client.post(reverse('mobetta:api:messagecomment-list'), postdata, format='json')

        self.assertEqual(response.status_code, 403)

    def test_fetch_comments(self):
        """
        Test how we fetch comments for a particular msgid/file combination.
        """
        msgid1 = u"String 1"
        msghash1 = get_hash_from_msgid_context(msgid1, '')

        msgid2 = u"String 2"
        msghash2 = get_hash_from_msgid_context(msgid2, '')

        MessageCommentFactory.create(
            translation_file=self.transfile,
            msghash=msghash1,
            body=u"First comment",
        )

        MessageCommentFactory.create(
            translation_file=self.transfile,
            msghash=msghash1,
            body=u"Second comment",
        )

        MessageCommentFactory.create(
            translation_file=self.transfile,
            msghash=msghash2,
            body=u"Third comment",
        )

        MessageCommentFactory.create(
            body=u"Other file comment"
        )

        client = APIClient()

        client.force_authenticate(user=self.admin_user)

        url = "{}?{}".format(
            reverse('mobetta:api:messagecomment-list'),
            urlencode({
                'translation_file': self.transfile.pk,
                'msghash': msghash1,
            })
        )

        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['msghash'], msghash1)
        self.assertEqual(response.data[0]['body'], u"First comment")
        self.assertEqual(response.data[0]['translation_file'], 1)
        self.assertEqual(response.data[1]['msghash'], msghash1)
        self.assertEqual(response.data[1]['body'], u"Second comment")
        self.assertEqual(response.data[1]['translation_file'], 1)

    def test_fetch_comments_unauthorised(self):
        """
        Make sure a non-admin user can't fetch comments.
        """
        client = APIClient()

        non_translator_user = UserFactory.create()

        client.force_authenticate(user=non_translator_user)

        msgid = u"String 1"
        msghash = get_hash_from_msgid_context(msgid, '')

        url = "{}?{}".format(
            reverse('mobetta:api:messagecomment-list'),
            urlencode({
                'translation_file': self.transfile.pk,
                'msghash': msghash,
            })
        )

        response = client.get(url, format='json')
        self.assertEqual(response.status_code, 403)


class TranslationSuggestionAPITests(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()

        self.admin_user = AdminFactory.create()

    @mock.patch('mobetta.util.get_automated_translation')
    @mock.patch('mobetta.util.get_translator')
    def test_get_translation(self, mock_get_translator, mock_get_automated_translation):
        # Set up the mock
        mock_get_translator.return_value = None
        mock_get_automated_translation.return_value = u"Automated translation"

        client = APIClient()

        client.force_authenticate(user=self.admin_user)

        url = "{}?{}".format(
            reverse('mobetta:api:translation_suggestion'),
            urlencode({
                'msgid': u"String to translate",
                'language_code': 'nl',
            })
        )

        response = client.get(url, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['suggestion'], u"Automated translation")
        self.assertEqual(response.data['msgid'], u"String to translate")
        self.assertEqual(response.data['language_code'], 'nl')

    @mock.patch('mobetta.util.get_automated_translation')
    @mock.patch('mobetta.util.get_translator')
    def test_get_translation_unauthorised(self, mock_get_translator, mock_get_automated_translation):
        # Set up the mock
        mock_get_translator.return_value = None
        mock_get_automated_translation.return_value = u"Automated translation"

        client = APIClient()

        non_admin_user = UserFactory.create()
        client.force_authenticate(user=non_admin_user)

        url = "{}?{}".format(
            reverse('mobetta:api:translation_suggestion'),
            urlencode({
                'msgid': u"String to translate",
                'language_code': 'nl',
            })
        )

        response = client.get(url, format='json')
        self.assertEqual(response.status_code, 403)
