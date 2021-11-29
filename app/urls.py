from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.index, name="index"),

    path('query/add', views.query_add, name="query_add"),
    path('query/my', views.query_list, name="query_list"),
    path('query/all', views.query_all, name="query_all"),
    path('query/file/<int:pk>', views.query_file_generate, name="query_file"),
    path('query/delete/<int:pk>', views.query_delete, name="query_delete"),
    path('query/<slug:slug>', views.query_detail, name="query_detail"),

    path('queries/', views.queries, name='queries'),
    path('query/<slug:slug>/places/', views.places, name='places'),
    path('query/<slug:slug>/edit/', views.query_edit, name='query_edit'),

    path('place/<str:cid>/edit', views.place_edit, name="place_edit"),
    path('place/<slug:slug>', views.place_detail, name="place_detail"),
    path('place/update/<int:pk>', views.place_update, name="place_update"),

    path('cabinet/<str:username>', views.public_cabinet, name="public_cabinet"),
    path('profile/', views.profile, name="profile"),
    path('reviews/', views.all_reviews, name="all_reviews"),
    path('my/reviews', views.my_reviews, name="my_reviews"),
    path('my/reviews/<int:pk>/edit', views.my_review_edit, name="my_review_edit"),
    path('registration/', views.registration, name="registration"),

    path('admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),

    path('admin_dashboard/tags', views.tags, name='tags'),
    path('admin_dashboard/tags/<slug:slug>/edit', views.tag_edit, name='tag_edit'),
    path('admin_dashboard/tags/<slug:slug>/delete', views.tag_delete, name='tag_delete'),

    path('admin_dashboard/groups/', views.group_list, name="group_list"),
    path('admin_dashboard/groups/not', views.group_not, name="group_not"),
    path('admin_dashboard/groups/<int:pk>', views.group_detail, name="group_detail"),

    path('admin_dashboard/review/types', views.review_types, name="review_types"),
    path('admin_dashboard/review/types/<int:pk>/edit', views.review_type_edit, name="review_type_edit"),

    path('admin_dashboard/users/', views.user_list, name="user_list"),
    path('admin_dashboard/users/<int:pk>', views.user_detail, name="user_detail"),
]





urlpatterns += [
    path('api/v1/tags', views.TagList.as_view(), name='tag_list_api'),
    path('api/v1/query/add', views.QueryAdd.as_view(), name='query_add_api'),
    path('api/v1/query/edit', views.QueryEdit.as_view(), name='query_edit_api'),
    path('api/v1/user/<str:username>/queries', views.QueryUser.as_view(), name='query_user_api'),
    path('api/v1/query/<slug:slug>/places', views.QueryPlaces.as_view(), name='query_places_api'),
    path('api/v1/query/<slug:slug>/detail', views.QueryDetail.as_view(), name='query_detail_api'),
    path('api/v1/place/<slug:slug>', views.PlaceDetail.as_view(), name='place_detail_api'),
    path('api/v1/review/<int:pk>', views.ReviewDetail.as_view(), name='review_detail_api'),
]
