from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class QueryTypeForm(forms.Form):
    name = forms.CharField(max_length=1000)
    page = forms.IntegerField(min_value=1, max_value=100)
    detail = forms.BooleanField()


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']