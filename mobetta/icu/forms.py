from django import forms

from .validators import validate_icu_syntax


class TranslationForm(forms.Form):
    msgid = forms.CharField(max_length=1024, widget=forms.HiddenInput())
    md5hash = forms.CharField(widget=forms.HiddenInput())
    translation = forms.CharField(
        widget=forms.Textarea(attrs={'cols': '80', 'rows': '3'}), required=False,
    )
    old_translation = forms.CharField(widget=forms.HiddenInput(), required=False)
    # occurrences = forms.CharField(
    #     widget=forms.Textarea(attrs={'readonly': 'readonly', 'rows': 4, 'cols': 15}),
    #     required=False
    # )

    def clean_translation(self):
        translation = self.cleaned_data['translation']
        try:
            validate_icu_syntax(translation)
        except forms.ValidationError as error:
            self.add_error('translation', error)
        return translation  # return the faulty translation so the end user can edit it

    def check_tokens(self):
        pass  # too complex for now

    def is_updated(self):
        translation = self.cleaned_data.get('translation')
        old_translation = self.cleaned_data.get('old_translation')
        return translation != old_translation

    def get_changes(self):
        old_val = self.cleaned_data['old_translation']
        new_val = self.cleaned_data['translation']
        assert old_val != new_val
        return [{
            'msgid': self.cleaned_data['msgid'],
            'md5hash': self.cleaned_data['md5hash'],
            'field': 'translation',
            'from': old_val,
            'to': new_val,
        }]
