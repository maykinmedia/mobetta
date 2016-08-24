# coding=utf8

from django.test import TestCase
from django.template import Template, Context

class MessageTagTests(TestCase):

    def test_highlight_tokens(self):
        template = Template("{% load message_tags %}{{ \"One token: {token}\"|highlight_tokens|safe }}")
        rendered = template.render(Context({}))

        self.assertEqual(rendered, "One token: <span class=\"format-token\">{token}</span>")
