from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'entries', views.DictionaryEntryViewSet, base_name='entry')

urlpatterns = [
    url(r'^', include(router.urls)),
]
