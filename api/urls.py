from . import views
from django.urls import path

app_name = 'api'

urlpatterns = [
   # path('query/<int:user_id>', views.QueryTypeAPI.as_view(), name='query'),
    path('query/<int:pk>/places', views.QueryAPI.as_view(), name='query_places'),
    path('query/<int:pk>', views.QueryDetailAPI.as_view(), name='query_detail'),
    path('place/<int:pk>', views.PlaceDetailAPI.as_view(), name='place_detail'),
    path('is_user/', views.UserDetailApi.as_view(), name='user_detail'),
]
