from django.conf.urls import include, url
from rest_framework import routers

from . import views

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'entries', views.DictionaryEntryViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
