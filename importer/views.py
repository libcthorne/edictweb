from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import DictionaryUploadForm
from .models import (
    DictionaryEntry,
    DictionaryImportRequest
)
from .tasks import start_dictionary_import

EDICT2_FILE = 'edict2'

def dictionary_upload(request):
    if request.method == 'GET':
        try:
            pending_import_request = DictionaryImportRequest.objects.get(completed=False)
            current_entries_count = DictionaryEntry.objects.count()
            total_entries_count = pending_import_request.total_entries_count
            progress = (current_entries_count/max(total_entries_count, 1))*100
            return HttpResponse("Import already in progress (%.2f%%) (cancel?)" % progress)
        except DictionaryImportRequest.DoesNotExist:
            form = DictionaryUploadForm()
            return render(request, 'importer/index.html', {'form': form})

    elif request.method == 'POST':
        form = DictionaryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # TODO: also check here if pending dictionary request
            # exists (in a way that isn't prone to race conditions)

            source_file = request.FILES['dictionary_file']

            with open(EDICT2_FILE, 'wb') as destination_file:
                for chunk in source_file.chunks():
                    destination_file.write(chunk)

            import_request = start_dictionary_import()

            return redirect('importer:dictionary-upload')
        else:
            return HttpResponse("Invalid form data")
