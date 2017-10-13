from django.http import HttpResponse
from django.shortcuts import render

from .forms import DictionaryUploadForm

def index(request):
    if request.method == 'GET':
        form = DictionaryUploadForm()
        return render(request, 'importer/index.html', {'form': form})

    elif request.method == 'POST':
        form = DictionaryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponse("Valid form data: %s" % request.FILES['dictionary_file'])
        else:
            return HttpResponse("Invalid form data")
