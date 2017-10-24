from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator,
)
from django.db.models import Count, IntegerField, Value
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

from importer.models import (
    DictionaryEntry,
    InvertedIndexWord,
)
from .forms import SearchForm

class SearchView(View):
    def get(self, request):
        form = SearchForm(request.GET)
        if not form.is_valid():
            return HttpResponseBadRequest("Invalid form data")

        query = form.cleaned_data['query']
        if not query:
            matching_entries = DictionaryEntry.objects.all()
            matching_entries = matching_entries.\
                               annotate(num_matches=Value(0, IntegerField())).\
                               order_by('id')

        else:
            normalized_words = [InvertedIndexWord.normalize(word) for word in query.split(' ')]
            matching_entries = DictionaryEntry.objects.filter(invertedindexentry__index_word__word__in=normalized_words).\
                               annotate(num_matches=Count('id')).\
                               order_by('-num_matches', 'id')

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
