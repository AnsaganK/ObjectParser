from django import forms


class QueryTypeForm(forms.Form):
    name = forms.CharField(max_length=1000)
    page = forms.IntegerField(min_value=1, max_value=100)