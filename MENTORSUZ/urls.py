from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('allauth.urls')),
    # Catch legacy prefixed auth URLs and redirect to non-prefixed (to satisfy Google OAuth)
    re_path(r'^(?P<lang>uz|ru|en)/accounts/(?P<path>.*)$', RedirectView.as_view(url='/accounts/%(path)s', permanent=True)),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('search/', include('edu_search.urls')),
    path('', include('mainapp.urls')),
)