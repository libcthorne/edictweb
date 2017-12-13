from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
    reverse,
)
from django.views import View

from edictweb import settings
from importer.models import DictionaryEntry

from . import queries
from .forms import SearchForm

class SearchView(View):
    def get(self, request):
        form = SearchForm(request.GET)
        if not form.is_valid():
            return HttpResponseBadRequest("Invalid form data")

        sequence_number = request.GET.get('seq_no')
        if sequence_number is not None:
            matching_entries = [get_object_or_404(
                DictionaryEntry,
                sequence_number=sequence_number,
            )]
            total_matches = 1
            matches_all_entries = True
        else:
            matching_entries, search_terms, total_matches = queries.search_entries(
                query=form.cleaned_data['query'],
                paginate=True,
                page=request.GET.get('page'),
            )

            matches_all_entries = len(search_terms) == 0

        if not matches_all_entries:
            matching_entries_jp_text_highlighted = queries.get_matching_entries_data_highlighted(
                matching_entries, search_terms, 'jp_text',
            )
            matching_entries_en_text_highlighted = queries.get_matching_entries_data_highlighted(
                matching_entries, search_terms, 'en_text',
            )

            for matching_entry in matching_entries:
                matching_entry.jp_text_highlighted = matching_entries_jp_text_highlighted[matching_entry]
                matching_entry.en_text_highlighted = matching_entries_en_text_highlighted[matching_entry]

        return render(request, 'searcher/index.html', {
            'form': form,
            'matches_all_entries': matches_all_entries,
            'paginated_matching_entries': matching_entries,
            'total_matches': total_matches,
            'site_url': settings.SITE_URL,
        })

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return redirect('searcher:index')

        return redirect("{}?query={}".format(reverse('searcher:index'), form.data.get('query')))
