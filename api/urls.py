from . import views
from django.urls import path

app_name = 'api'

urlpatterns = [
    path('query_type/<int:user_id>', views.QueryTypeAPI.as_view(), name='query_type'),
    path('query_type/<int:pk>/queries', views.QueryAPI.as_view(), name='query_type_queries'),
    path('query_type/<int:pk>', views.QueryTypeDetailAPI.as_view(), name='query_type_detail'),
    path('query/<int:pk>', views.QueryDetailAPI.as_view(), name='query_detail'),
    path('is_user/', views.UserDetailApi.as_view(), name='user_detail'),
]
