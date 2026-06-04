from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('allauth.urls')),
    # Catch legacy prefixed auth URLs and redirect to non-prefixed (to satisfy Google OAuth)
    re_path(r'^(?P<lang>uz|ru|en)/accounts/(?P<path>.*)$', RedirectView.as_view(url='/accounts/%(path)s', permanent=True)),
    # API endpointlar — i18n prefikssiz (til prefeksi kerak emas)
    path('api/', include('mainapp.api_urls')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('search/', include('edu_search.urls')),
    path('', include('mainapp.urls')),
)

# [Y-4] Media fayllarni uzatish (development uchun)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)