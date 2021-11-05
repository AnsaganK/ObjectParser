from django.contrib.auth.models import User
from rest_framework import serializers
from app.models import Query, Place, QueryPlace


class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = '__all__'


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'


class QueryPlaceSerializer(serializers.ModelSerializer):
    place = PlaceSerializer()
    class Meta:
        model = QueryPlace
        fields = ['place']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')