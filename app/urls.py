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

    path('place/<str:cid>/review/add', views.review_add, name="review_add"),
    path('place/<slug:slug>', views.place_detail, name="place_detail"),
    path('place/update/<int:pk>', views.place_update, name="place_update"),

    path('profile/', views.profile, name="profile"),
    path('reviews/', views.all_reviews, name="all_reviews"),
    path('my/reviews', views.my_reviews, name="my_reviews"),
    path('my/reviews/<int:pk>/edit', views.my_review_edit, name="my_review_edit"),
    path('registration/', views.registration, name="registration"),

    path('admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),

    path('admin_dashboard/groups/', views.group_list, name="group_list"),
    path('admin_dashboard/groups/not', views.group_not, name="group_not"),
    path('admin_dashboard/groups/<int:pk>', views.group_detail, name="group_detail"),

    path('admin_dashboard/users/', views.user_list, name="user_list"),
    path('admin_dashboard/users/<int:pk>', views.user_detail, name="user_detail"),
]


urlpatterns += [
    path('api/v1/query/add', views.QueryAdd.as_view(), name='query_add'),
    path('api/v1/query/<str:username>', views.QueryUser.as_view(), name='query_user'),
    path('api/v1/query/<int:pk>', views.QueryAdd.as_view(), name='query_detail'),
    path('api/v1/query/<int:pk>/places', views.QueryAdd.as_view(), name='query_places'),
]