import re

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from mobetta.models import MessageComment, TranslationFile
from mobetta.util import get_token_regexes

ProjectUserModel = get_user_model()


class TranslationForm(forms.Form):
    msgid = forms.CharField(max_length=1024, widget=forms.HiddenInput())
    md5hash = forms.CharField(max_length=32, widget=forms.HiddenInput())
    translation = forms.CharField(widget=forms.Textarea(attrs={'cols': '80', 'rows': '3'}), required=False)
    old_translation = forms.CharField(widget=forms.HiddenInput(), required=False)
    fuzzy = forms.BooleanField(required=False)
    old_fuzzy = forms.BooleanField(required=False, widget=forms.HiddenInput())
    context = forms.CharField(max_length=1024, required=False)
    occurrences = forms.CharField(
        widget=forms.Textarea(attrs={'readonly': 'readonly', 'rows': 4, 'cols': 15}),
        required=False
    )

    def clean(self):
        cleaned_data = super(TranslationForm, self).clean()

        regex = '|'.join(get_token_regexes())

        source_format_tokens = re.findall(regex, cleaned_data['msgid'])
        translation_format_tokens = re.findall(regex, cleaned_data['translation'])

        # Check if there is the same number of formating tokens in the source and the translation.
        if len(source_format_tokens) != len(translation_format_tokens) and cleaned_data['translation']:
            error = 'There should be {} formating token(s) in the source text and the translation.'
            tokens = len(source_format_tokens)
            raise forms.ValidationError(error.format(tokens))

    def is_updated(self):
        translation = self.cleaned_data.get('translation')
        old_translation = self.cleaned_data.get('old_translation')
        fuzzy = self.cleaned_data.get('fuzzy')
        old_fuzzy = self.cleaned_data.get('old_fuzzy')

        return (translation != old_translation) or (fuzzy != old_fuzzy)

    def get_changes(self):
        changes = []

        for fieldname in ['translation', 'fuzzy']:
            old_val = self.cleaned_data.get("old_{}".format(fieldname))
            new_val = self.cleaned_data.get(fieldname)
            if new_val != old_val:
                changes.append({
                    'msgid': self.cleaned_data['msgid'],
                    'md5hash': self.cleaned_data['md5hash'],
                    'field': fieldname,
                    'from': old_val,
                    'to': new_val,
                })

        return changes


class CommentForm(forms.ModelForm):
    translation_file = forms.ModelChoiceField(queryset=TranslationFile.objects.all(), widget=forms.HiddenInput())
    msghash = forms.CharField(max_length=32, widget=forms.HiddenInput())
    body = forms.CharField(widget=forms.Textarea(attrs={'cols': '120', 'rows': '8'}))

    class Meta:
        model = MessageComment
        fields = ['translation_file', 'msghash', 'body']


class AddTranslatorForm(forms.Form):
    user = forms.ModelChoiceField(queryset=ProjectUserModel.objects.all())
    language = forms.ChoiceField(choices=settings.LANGUAGES)

    def save(self, *args, **kwargs):
        user = self.cleaned_data.get('user')
        language = self.cleaned_data.get('language')

        group, created = Group.objects.get_or_create(name='translators-%s' % language)

        user.groups.add(group)
