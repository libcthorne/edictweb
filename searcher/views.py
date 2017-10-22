from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator,
)
from django.shortcuts import render

from importer.models import DictionaryEntry

def index(request):
    all_entries = DictionaryEntry.objects.all().order_by('id')
    paginator = Paginator(all_entries, per_page=20)

    page = request.GET.get('page')
    try:
        entries = paginator.page(page)
    except PageNotAnInteger:
        entries = paginator.page(1)
    except EmptyPage:
        entries = paginator.page(paginator.num_pages)

    return render(request, 'searcher/index.html', {'entries': entries})
