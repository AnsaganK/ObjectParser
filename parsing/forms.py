from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from parsing.models import Review, Place, Tag, Query, ReviewType, Profile


class QueryForm(forms.Form):
    name = forms.CharField(max_length=1000)
    not_all = forms.BooleanField(required=False)
    page = forms.IntegerField(min_value=1, required=False, max_value=1000)
    # detail = forms.BooleanField(required=False)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text', 'rating']


class ReviewTypeForm(forms.ModelForm):
    class Meta:
        model = ReviewType
        fields = ['name']


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1']


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class UserDetailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'groups']


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ['name', 'description', 'meta', 'title', 'is_redirect', 'redirect']


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'path']


class QueryContentForm(forms.ModelForm):
    class Meta:
        model = Query
        fields = ['content', 'tags', 'access']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user']
