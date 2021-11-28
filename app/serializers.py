from django.contrib.auth.models import User
from rest_framework import serializers
from app.models import Query, Place, QueryPlace, PlacePhoto, Tag, Review, ReviewPart, ReviewType
import re

from constants import SERVER_NAME


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name', 'id']


class QuerySerializer(serializers.ModelSerializer):
    places_count = serializers.ReadOnlyField()
    base_img = serializers.ReadOnlyField()
    tags = TagSerializer(many=True)

    class Meta:
        model = Query
        fields = ['name', 'slug', 'places_count', 'base_img', 'tags', 'content']


class ReviewTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewType
        fields = ['name']


class ReviewPartSerializer(serializers.ModelSerializer):
    review_type = ReviewTypeSerializer()

    class Meta:
        model = ReviewPart
        fields = ['review_type', 'rating']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    parts = ReviewPartSerializer(many=True)
    get_rating = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = ['author_name', 'author_link', 'author_img_link', 'rating', 'text', 'user', 'is_google', 'parts',
                  'get_rating']


class PlacePhotoSerializer(serializers.ModelSerializer):
    img = serializers.SerializerMethodField('get_img')

    def get_img(self, obj):
        return SERVER_NAME + obj.img.url

    class Meta:
        model = PlacePhoto
        fields = ['img']


class PlaceSerializer(serializers.ModelSerializer):
    get_meta_description = serializers.ReadOnlyField()
    get_img = serializers.ReadOnlyField()
    get_more_text = ReviewSerializer(many=False)
    reviews = ReviewSerializer(many=True)
    photos = PlacePhotoSerializer(many=True)

    class Meta:
        model = Place
        fields = ['name', 'slug', 'cid', 'rating', 'img', 'address', 'phone_number', 'site',
                  'description', 'meta', 'date_create', 'get_meta_description', 'reviews',
                  'photos', 'rating_user_count', 'title', 'get_more_text', 'get_img', 'coordinate_html']


class PlaceMinSerializer(serializers.ModelSerializer):
    get_meta_description = serializers.ReadOnlyField()

    class Meta:
        model = Place
        fields = ['name', 'slug', 'cid', 'rating', 'img', 'address', 'phone_number', 'site', 'meta',
                  'get_meta_description', 'description']


class QueryPlaceSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(many=True)

    class Meta:
        model = QueryPlace
        fields = ['place']
