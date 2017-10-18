from django.conf.urls import url

from . import views

app_name = 'importer'

urlpatterns = [
    url(
        r'^$',
        views.dictionary_upload,
        name='dictionary-upload'
    ),
    url(
        r'^progress/(?P<import_request_id>[0-9]+)$',
        views.dictionary_import_progress,
        name='dictionary-import-progress'
    )
]
