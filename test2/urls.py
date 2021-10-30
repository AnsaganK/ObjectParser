from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from django.contrib.auth import views as acc
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls', namespace='api')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include('app.urls', namespace='app')),
]

urlpatterns += [
    path('accounts/login/', acc.LoginView.as_view(), name='login'),
    path('accounts/logout/', acc.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )