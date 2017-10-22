from django.conf.urls import url

from . import views

app_name = 'importer'

urlpatterns = [
    url(r'^(?:import/)?$', views.DictionaryImport.as_view(), name='import'),
    url(r'^cancel$', views.DictionaryImportCancel.as_view(), name='cancel'),
]
