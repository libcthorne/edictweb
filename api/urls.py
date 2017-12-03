from django.conf.urls import include, url
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

app_name = 'api'

urlpatterns = [
    url(r'^entries/$', views.DictionaryEntryList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
