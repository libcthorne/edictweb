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

        results = queries.paginated_search(
            query=form.cleaned_data['query'],
            page=request.GET.get('page'),
        )

        return render(request, 'searcher/index.html', {
            'form': form,
            'matches_all_entries': results['matches_all_entries'],
            'paginated_matching_entries': results['paginated_matching_entries'],
            'total_matches': results['total_matches'],
        })

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return redirect('searcher:index')

        return redirect("{}?query={}".format(reverse('searcher:index'), form.data.get('query')))
