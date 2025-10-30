from django.contrib.sitemaps import Sitemap
from .models import Homework


class HomeworkSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Homework.published.all()

    def lastmod(self, obj):
        return obj.updated