from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.index, name="index"),

    path('query_type/add', views.query_type_add, name="query_type_add"),
    path('query_type/', views.query_type_list, name="query_type_list"),
    path('query_type/file/<int:pk>', views.query_type_file_generate, name="query_type_file"),
    path('query_type/delete/<int:pk>', views.query_type_delete, name="query_type_delete"),
    path('query_type/<int:pk>', views.query_type_detail, name="query_type_detail"),

    path('query/<int:pk>', views.query_detail, name="query_detail"),
    path('query/update/<int:pk>', views.query_update, name="query_update"),

    path('profile/', views.profile, name="profile"),
    path('registration/', views.registration, name="registration"),

    path('admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),

    path('admin_dashboard/groups/', views.group_list, name="group_list"),
    path('admin_dashboard/groups/not', views.group_not, name="group_not"),
    path('admin_dashboard/groups/<int:pk>', views.group_detail, name="group_detail"),

    path('admin_dashboard/users/', views.user_list, name="user_list"),
    path('admin_dashboard/users/<int:pk>', views.user_detail, name="user_detail"),
]
