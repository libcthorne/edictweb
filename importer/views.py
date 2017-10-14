from django.http import HttpResponse
from django.shortcuts import render

from .forms import DictionaryUploadForm

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

            return HttpResponse("Dictionary uploaded")
        else:
            return HttpResponse("Invalid form data")
