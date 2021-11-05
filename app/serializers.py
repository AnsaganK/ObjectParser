from django.contrib.auth.models import User
from rest_framework import serializers
from app.models import Query, Place, QueryPlace
import re


class QuerySerializer(serializers.ModelSerializer):
    places_count = serializers.SerializerMethodField('places_count')
    base_img = serializers.SerializerMethodField('base_img')

    def base_img(self, obj):
        places = obj.places.all()
        if len(places) > 0:
            place = places[0]
            if place and place.img:
                return place.img.url
        return 'http://170.130.40.103/static/img/not_found.png'

    def places_count(self, obj):
        return Place.objects.filter(queries__query_id=Query.id).count()

    class Meta:
        model = Query
        fields = ['name', 'slug', 'places_count', 'base_img']




class PlaceSerializer(serializers.ModelSerializer):
    get_meta_description = serializers.SerializerMethodField('get_meta_description')

    def get_meta_description(self, obj):
        if obj.meta == None:
            return None
        pattern = r'(?<=content=")(.+?)(?=")'
        meta = re.search(pattern, obj.meta)
        if meta:
            return meta.group()
        return ' - '

    class Meta:
        model = Place
        fields = ['name', 'slug', 'cid', 'rating', 'img', 'address', 'phone_number', 'site', 'description', 'meta', 'date_create', 'get_meta_description']

class PlaceMinSerializer(serializers.ModelSerializer):
    get_meta_description = serializers.SerializerMethodField('get_meta_description')

    def get_meta_description(self, obj):
        if obj.meta == None:
            return None
        pattern = r'(?<=content=")(.+?)(?=")'
        meta = re.search(pattern, obj.meta)
        if meta:
            return meta.group()
        return ' - '

    class Meta:
        model = Place
        fields = ['name', 'slug', 'cid', 'rating', 'img', 'address', 'phone_number', 'site', 'meta', 'get_meta_description']



class QueryPlaceSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(many=True)

    class Meta:
        model = QueryPlace
        fields = ['place']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')