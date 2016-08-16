from django import forms

class TranslationForm(forms.Form):
    msgid = forms.CharField(max_length=1024, widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    translation = forms.CharField(max_length=1024)
