from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(required=False)
    query.widget.attrs['class'] = "form-control"
