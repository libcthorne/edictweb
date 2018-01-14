from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils.decorators import method_decorator
from django.views import View

from .const import DICTIONARY_FILE
from .forms import DictionaryUploadForm
from .models import (
    DictionaryEntry,
    DictionaryImportRequest,
    PendingDictionaryImportRequest,
)
from .tasks import cancel_pending_import

user_is_staff = user_passes_test(lambda u: u.is_staff, login_url='accounts:staff-login-prompt')

@method_decorator(user_is_staff, name='dispatch')
class DictionaryImport(View):
    def get(self, request):
        pending_import_request = PendingDictionaryImportRequest.objects.\
                                 select_related('import_request').first()

        if pending_import_request.import_request:
            # Import already running

            current_entries_count = DictionaryEntry.objects.count()

            if pending_import_request.import_request.started:
                progress = current_entries_count
            else:
                progress = 0

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

            with open(DICTIONARY_FILE, 'wb') as destination_file:
                for chunk in source_file.chunks():
                    destination_file.write(chunk)

            import_request = DictionaryImportRequest()
            import_request.save()

            pending_import_request.import_request = import_request
            pending_import_request.save()

            return redirect('importer:import')

@method_decorator(user_is_staff, name='dispatch')
class DictionaryImportCancel(View):
    def get(self, request):
        form = forms.Form()
        return render(request, 'importer/cancel.html', {'form': form})

    def post(self, request):
        cancel_pending_import()
        return redirect('importer:import')
