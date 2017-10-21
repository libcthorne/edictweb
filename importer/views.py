from django import forms
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import DictionaryUploadForm
from .models import (
    DictionaryEntry,
    DictionaryImportRequest,
    PendingDictionaryImportRequest,
)

EDICT2_FILE = 'edict2'

def dictionary_upload(request):
    if request.method == 'GET':
        pending_import_request = PendingDictionaryImportRequest.objects.select_related('import_request').first()
        if pending_import_request.import_request:
            current_entries_count = DictionaryEntry.objects.filter(source_import_request=pending_import_request.import_request).count()
            total_entries_count = pending_import_request.import_request.total_entries_count
            progress = (current_entries_count/max(total_entries_count, 1))*100
            return HttpResponse("Import in progress (%.2f%%) (<a href='cancel'>cancel?</a>)" % progress)

        # No task running
        form = DictionaryUploadForm()
        return render(request, 'importer/index.html', {'form': form})

    elif request.method == 'POST':
        form = DictionaryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                pending_import_request = PendingDictionaryImportRequest.objects.select_for_update().first()
                if pending_import_request.import_request_id:
                    return HttpResponse("Import already in progress")

                source_file = request.FILES['dictionary_file']

                with open(EDICT2_FILE, 'wb') as destination_file:
                    for chunk in source_file.chunks():
                        destination_file.write(chunk)

                import_request = DictionaryImportRequest()
                import_request.save()

                pending_import_request.import_request = import_request
                pending_import_request.save()

                return redirect('importer:dictionary-upload')
        else:
            return HttpResponse("Invalid form data")

def import_cancel(request):
    if request.method == 'GET':
        form = forms.Form()
        return render(request, 'importer/cancel.html', {'form': form})
    elif request.method == 'POST':
        with transaction.atomic():
            pending_import_request = PendingDictionaryImportRequest.objects.select_for_update().first()
            if pending_import_request.import_request_id and pending_import_request.import_request.delete():
                return HttpResponse("Import cancelled")

            return HttpResponse("Import currently not running")
