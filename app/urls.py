from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name="index"),

    path('query_type/add', views.query_type_add, name="query_type_add"),
    path('query_type/', views.query_type_list, name="query_type_list"),
    path('query_type/<int:pk>', views.query_type_detail, name="query_type_detail"),

    path('query/<int:pk>', views.query_detail, name="query_detail"),

    path('profile/', views.profile, name="profile"),
    path('registration/', views.registration, name="registration")
]