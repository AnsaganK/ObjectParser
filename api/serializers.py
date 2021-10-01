from django.contrib.auth.models import User
from rest_framework import serializers
from app.models import QueryType, Query


class QueryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryType
        fields = ('id', 'user', 'name', 'page', 'date_create', 'status')


class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Query
        fields = ('id', 'place_id', 'date_create', 'date_update', 'get_rating')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')