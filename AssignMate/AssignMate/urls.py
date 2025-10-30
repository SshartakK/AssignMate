from django.urls import path, include
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from assign.sitemaps import HomeworkSitemap
from django.conf import settings
from django.conf.urls.static import static


sitemaps = {
    'homeworks': HomeworkSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('assign.urls', namespace='assign')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)