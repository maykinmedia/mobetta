# coding=utf8

from django.template import Context, Template
from django.test import TestCase


class MessageTagTests(TestCase):

    def test_highlight_tokens(self):
        template = Template("{% load message_tags %}{{ \"One token: {token}\"|highlight_tokens|safe }}")
        rendered = template.render(Context({}))

        self.assertEqual(rendered, "One token: <span class=\"format-token\">{token}</span>")
