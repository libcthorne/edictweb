from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator,
)
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import (
    redirect,
    render,
    reverse,
)
from django.views import View

from importer.models import DictionaryEntry
from .forms import SearchForm

class SearchView(View):
    def get(self, request):
        form = SearchForm(request.GET)
        if not form.is_valid():
            return HttpResponseBadRequest("Invalid form data")

        query = form.cleaned_data['query']
        if not query:
            matching_entries = DictionaryEntry.objects.all()
        else:
            matching_entries = DictionaryEntry.objects.filter(edict_data__icontains=query)

        matching_entries = matching_entries.order_by('id')
        paginator = Paginator(matching_entries, per_page=20)

        page = request.GET.get('page')
        try:
            entries = paginator.page(page)
        except PageNotAnInteger:
            entries = paginator.page(1)
        except EmptyPage:
            entries = paginator.page(paginator.num_pages)

        return render(request, 'searcher/index.html', {'form': form, 'entries': entries})

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return redirect('searcher:index')

        return redirect("{}?query={}".format(reverse('searcher:index'), form.data.get('query')))
