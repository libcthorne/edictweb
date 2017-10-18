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
        form = DictionaryUploadForm()
        return render(request, 'importer/index.html', {'form': form})

    elif request.method == 'POST':
        form = DictionaryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            source_file = request.FILES['dictionary_file']

            with open(EDICT2_FILE, 'wb') as destination_file:
                for chunk in source_file.chunks():
                    destination_file.write(chunk)

            import_request = start_dictionary_import()

            return redirect('importer:dictionary-import-progress', import_request_id=import_request.id)
        else:
            return HttpResponse("Invalid form data")

def dictionary_import_progress(request, import_request_id):
    if request.method == 'GET':
        import_request = get_object_or_404(DictionaryImportRequest, id=import_request_id)

        if not import_request.started:
            return HttpResponse("Dictionary import not started yet")
        elif import_request.interrupted:
            return HttpResponse("Dictionary import interrupted")
        elif not import_request.completed:
            current_entries_count = DictionaryEntry.objects.count()
            total_entries_count = import_request.total_entries_count
            progress = (current_entries_count/total_entries_count)*100
            return HttpResponse("Dictionary import progress for task %d: %.2f%%" % (import_request.id, progress))
        else:
            return HttpResponse("Dictionary import completed")
