from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils.decorators import method_decorator
from django.views import View

from .forms import DictionaryUploadForm
from .models import (
    DictionaryEntry,
    DictionaryImportRequest,
    PendingDictionaryImportRequest,
)

EDICT2_FILE = 'edict2'

@method_decorator(login_required, name='dispatch')
class DictionaryImport(View):
    def get(self, request):
        pending_import_request = PendingDictionaryImportRequest.objects.\
                                 select_related('import_request').first()

        if pending_import_request.import_request:
            # Import already running
            current_entries_count = DictionaryEntry.objects.\
                                    filter(source_import_request=pending_import_request.import_request).\
                                    count()
            total_entries_count = pending_import_request.import_request.total_entries_count
            progress = (current_entries_count/max(total_entries_count, 1))*100
            return render(request, 'importer/progress.html', {'progress': progress})
        else:
            # No import currently running
            form = DictionaryUploadForm()
            return render(request, 'importer/upload.html', {'form': form})

    def post(self, request):
        form = DictionaryUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'importer/upload.html', {'form': form})

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

            return redirect('importer:import')


@method_decorator(login_required, name='dispatch')
class DictionaryImportCancel(View):
    def get(self, request):
        form = forms.Form()
        return render(request, 'importer/cancel.html', {'form': form})

    def post(self, request):
        with transaction.atomic():
            pending_import_request = PendingDictionaryImportRequest.objects.select_for_update().first()
            if pending_import_request.import_request_id and pending_import_request.import_request.delete():
                return redirect('importer:import')
            else:
                return HttpResponse("Import not running")
