import re

from django import forms

class TranslationForm(forms.Form):
    msgid = forms.CharField(max_length=1024, widget=forms.TextInput(attrs={'readonly': 'readonly', 'size': '80'}))
    translation = forms.CharField(max_length=1024, widget=forms.TextInput(attrs={'size': '80'}), required=False)
    old_translation = forms.CharField(max_length=1024, widget=forms.HiddenInput(), required=False)
    fuzzy = forms.BooleanField(required=False)
    old_fuzzy = forms.BooleanField(required=False, widget=forms.HiddenInput())
    context = forms.CharField(max_length=1024, required=False)
    old_context = forms.CharField(max_length=1024, widget=forms.HiddenInput(), required=False)

    def clean(self):
        cleaned_data = super(TranslationForm, self).clean()

        regex = r'{(?:[a-zA-z]*|[0-9]*)}'

        original_format_tokens = re.findall(regex, cleaned_data['msgid'])
        translation_format_tokens = re.findall(regex, cleaned_data['translation'])
        missing_tokens = set(original_format_tokens) ^ set(translation_format_tokens)

        if missing_tokens and cleaned_data['translation']:
            error = 'The following tokens should be present in both the source text and the translation : {}.'
            tokens = ', '.join([t for t in missing_tokens])

            raise forms.ValidationError(error.format(tokens))

    def is_updated(self):
        translation = self.cleaned_data.get('translation')
        old_translation = self.cleaned_data.get('old_translation')
        fuzzy = self.cleaned_data.get('fuzzy')
        old_fuzzy = self.cleaned_data.get('old_fuzzy')
        context = self.cleaned_data.get('context')
        old_context = self.cleaned_data.get('old_context')

        return (translation != old_translation) or (fuzzy != old_fuzzy) or (context != old_context)

    def get_changes(self):
        changes = []

        for fieldname in ['translation', 'fuzzy', 'context']:
            old_val = self.cleaned_data.get("old_{}".format(fieldname))
            new_val = self.cleaned_data.get(fieldname)
            if new_val != old_val:
                changes.append({
                    'msgid': self.cleaned_data['msgid'],
                    'field': fieldname,
                    'from': old_val,
                    'to': new_val,
                })

        return changes
