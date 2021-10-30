from django.contrib import admin
from .models import Query, Place, Profile, QueryPlace, Review


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'places_count']
    list_display_links = ['id', 'name']
    list_filter = ['user']


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'cid', 'name', 'img_url']
    list_display_links = ['id', 'place_id']
    # list_filter = ['query']

admin.site.register(Profile)
admin.site.register(QueryPlace)
admin.site.register(Review)