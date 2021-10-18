from django.contrib.auth.models import User
from rest_framework import serializers
from app.models import Query, Place


class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = ('id', 'user', 'name', 'page', 'date_create', 'status')


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ('id', 'place_id', 'date_create', 'date_update', 'get_rating')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')