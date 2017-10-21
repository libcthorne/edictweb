from django.conf.urls import url

from . import views

app_name = 'importer'

urlpatterns = [
    url(
        r'^$',
        views.DictionaryImport.as_view(),
        name='dictionary-import'
    ),
    url(
        r'^cancel$',
        views.DictionaryImportCancel.as_view(),
        name='dictionary-import-cancel'
    ),
]
