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
from importer import const
from importer.models import DictionaryEntry

from . import (
    queries,
    util,
)
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
            should_highlight = False
        else:
            matching_entries, search_terms, total_matches = queries.search_entries(
                query=form.cleaned_data['query'],
                paginate=True,
                page=request.GET.get('page'),
            )
            should_highlight = len(search_terms) > 0

        if should_highlight:
            matching_entries_jp_text_highlighted = util.get_matching_entries_data_highlighted(
                matching_entries, search_terms, 'jp_text', const.JP_TEXT_DESCRIPTION_SEPARATOR
            )
            matching_entries_en_text_highlighted = util.get_matching_entries_data_highlighted(
                matching_entries, search_terms, 'en_text', const.EN_TEXT_DESCRIPTION_SEPARATOR
            )

            for matching_entry in matching_entries:
                matching_entry.jp_text_highlighted = matching_entries_jp_text_highlighted[matching_entry]
                matching_entry.en_text_highlighted = matching_entries_en_text_highlighted[matching_entry]

        return render(request, 'searcher/index.html', {
            'form': form,
            'should_highlight': should_highlight,
            'paginated_matching_entries': matching_entries,
            'total_matches': total_matches,
            'site_url': settings.SITE_URL,
            'debug': request.GET.get('debug'),
        })

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return redirect('searcher:index')

        return redirect("{}?query={}".format(reverse('searcher:index'), form.data.get('query')))
