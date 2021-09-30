from django.contrib import admin
from .models import Query, QueryType, Profile


@admin.register(QueryType)
class QueryTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'query_count']
    list_display_links = ['id', 'name']
    list_filter = ['user']


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'place_id']
    list_display_links = ['id', 'place_id']
    list_filter = ['type']

admin.site.register(Profile)