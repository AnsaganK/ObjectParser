from django.contrib.auth.models import User
from rest_framework import serializers
from app.models import Query, Place, QueryPlace


class QuerySerializer(serializers.ModelSerializer):
    places_count = serializers.SerializerMethodField('places_count')
    base_img = serializers.SerializerMethodField('base_img')

    def base_img(self):
        place = Place.objects.filter(queries__query_id=Query.id).first()
        if place:
            return place.img.url
        else:
            return 'http://170.130.40.103/static/img/not_found.png'
    def places_count(self):
        return Place.objects.filter(queries__query_id=Query.id).count()

    class Meta:
        model = Query
        fields = ['name', 'slug', 'places_count', 'base_img']


class PlaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Place
        fields = ['name', 'slug', 'cid', 'rating', 'img', 'address', 'phone_number', 'site', 'description', 'meta', 'date_create']


class QueryPlaceSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(many=True)

    class Meta:
        model = QueryPlace
        fields = ['place']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')