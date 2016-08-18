from django import forms

class TranslationForm(forms.Form):
    msgid = forms.CharField(max_length=1024, widget=forms.TextInput(attrs={'readonly': 'readonly', 'size': '80'}))
    translation = forms.CharField(max_length=1024, widget=forms.TextInput(attrs={'size': '80'}), required=False)
    old_translation = forms.CharField(max_length=1024, widget=forms.HiddenInput(), required=False)
    fuzzy = forms.BooleanField(required=False)
    old_fuzzy = forms.BooleanField(required=False, widget=forms.HiddenInput())
