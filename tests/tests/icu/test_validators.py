from __future__ import absolute_import, unicode_literals

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from mobetta.icu.validators import validate_icu_syntax


class ValidatorTests(SimpleTestCase):

    def assertValidMessageSyntax(self, msg):
        try:
            validate_icu_syntax(msg)
        except ValidationError as error:
            self.fail("Message '%s' should be valid, got instead: '%s'" % (msg, error))

    def test_valid_syntaxes(self):
        self.assertValidMessageSyntax('Hello everyone')
        self.assertValidMessageSyntax('Hello {who}')
        self.assertValidMessageSyntax('I have {numCats, number} cats.')
        self.assertValidMessageSyntax('Almost {pctBlack, number, percent} of them are black.')
        self.assertValidMessageSyntax('Sale begins {start, date, medium}')
        self.assertValidMessageSyntax('Coupon expires at {expires, time, short}')
        self.assertValidMessageSyntax("Escaped '{' brace")
        self.assertValidMessageSyntax("Unclosed closing } brace")

    def test_valid_select_syntaxes(self):
        msg1 = ('{gender, select,'
                '    male {He}'
                '    female {She}'
                '    other {They}'
                '} will respond shortly.')
        self.assertValidMessageSyntax(msg1)

        msg2 = ('{taxableArea, select,'
                '    yes {An additional {taxRate, number, percent} tax will be collected.}'
                '    other {No taxes apply.}'
                '}')
        self.assertValidMessageSyntax(msg2)

    def test_valid_plural_syntaxes(self):
        """
        Assert that the plural formats are correctly validated.

        Ref: https://formatjs.io/guides/message-syntax/#plural-format
        """
        msg1 = ('Cart: {itemCount} {itemCount, plural,'
                '    one {item}'
                '    other {items}'
                '}')
        self.assertValidMessageSyntax(msg1)

        msg2 = ('You have {itemCount, plural,'
                '    =0 {no items}'
                '    one {1 item}'
                '    other {{itemCount} items}'
                '}.')
        self.assertValidMessageSyntax(msg2)

        msg3 = ('You have {itemCount, plural,'
                '    =0 {no items}'
                '    one {# item}'
                '    other {# items}'
                '}.')
        self.assertValidMessageSyntax(msg3)

    def test_valid_selectordinal_syntaxes(self):
        """
        Assert that the selectordinal syntax is validated correctly.

        Ref: https://formatjs.io/guides/message-syntax/#selectordinal-format
        """
        msg = ("It's my cat's {year, selectordinal,"
               "    one {#st}"
               "    two {#nd}"
               "    few {#rd}"
               "    other {#th}"
               "} birthday!")
        self.assertValidMessageSyntax(msg)

    # def test_custom_formats(self):
    #     """
    #     Assert that custom formats are considered valid messages.
    #     """
    #     raise NotImplementedError

    def test_invalid_syntax(self):
        with self.assertRaises(ValidationError):
            validate_icu_syntax('Unclosed brace {')

        with self.assertRaises(ValidationError) as error:
            validate_icu_syntax('I have {numCats, unknownFormat} cats.')
        self.assertEqual(error.exception.params['error_detail'], 'Illegal argument')
