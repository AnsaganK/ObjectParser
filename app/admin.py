from django.contrib import admin
from .models import Query, Place, Profile, QueryPlace, Review, Tag, ReviewType, ReviewPart


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'places_count']
    list_display_links = ['id', 'name']
    list_filter = ['user']


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'cid', 'name', 'img_url']
    list_display_links = ['id']
    # list_filter = ['query']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ReviewType)
class ReviewTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(ReviewPart)
class ReviewPartAdmin(admin.ModelAdmin):
    list_display = ['id', 'rating']


admin.site.register(Profile)
admin.site.register(QueryPlace)
admin.site.register(Review)
