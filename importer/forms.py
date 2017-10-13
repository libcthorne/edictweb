from django import forms

class DictionaryUploadForm(forms.Form):
    dictionary_file = forms.FileField(label='File')
