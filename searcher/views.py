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

from . import queries
from .forms import SearchForm

class SearchView(View):
    def get(self, request):
        form = SearchForm(request.GET)
        if not form.is_valid():
            return HttpResponseBadRequest("Invalid form data")

        matching_entries, search_terms, total_matches = queries.search_entries(
            query=form.cleaned_data['query'],
            paginate=True,
            page=request.GET.get('page'),
        )

        matches_all_entries = len(search_terms) == 0
        if not matches_all_entries:
            matching_entries_data_highlighted = queries.get_matching_entries_data_highlighted(matching_entries, search_terms)
            for matching_entry in matching_entries:
                matching_entry.edict_data_highlighted = matching_entries_data_highlighted[matching_entry]

        return render(request, 'searcher/index.html', {
            'form': form,
            'matches_all_entries': matches_all_entries,
            'paginated_matching_entries': matching_entries,
            'total_matches': total_matches,
        })

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return redirect('searcher:index')

        return redirect("{}?query={}".format(reverse('searcher:index'), form.data.get('query')))
