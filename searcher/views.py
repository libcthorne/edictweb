from datetime import datetime

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
from mongoengine import connect

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

        query_start = datetime.now()

        sequence_number = request.GET.get('seq_no')
        if sequence_number is not None:
            try:
                matching_entries = [
                    DictionaryEntry.objects.get(
                        sequence_number=sequence_number,
                    )
                ]
            except DictionaryEntry.DoesNotExist:
                raise Http404

            total_matches = 1
            should_highlight = False
        else:
            matching_entries, search_terms, total_matches = queries.search_entries(
                query=form.cleaned_data['query'],
                page=request.GET.get('page'),
            )
            should_highlight = len(search_terms) > 0

        query_end = datetime.now()

        if should_highlight:
            for matching_entry in matching_entries:
                matching_entry.jp_text_highlighted = util.get_text_highlighted(
                    matching_entry.jp_text,
                    const.JP_TEXT_DESCRIPTION_SEPARATOR,
                    search_terms,
                )
                matching_entry.en_text_highlighted = util.get_text_highlighted(
                    matching_entry.en_text,
                    const.EN_TEXT_DESCRIPTION_SEPARATOR,
                    search_terms,
                )

        return render(request, 'searcher/index.html', {
            'form': form,
            'should_highlight': should_highlight,
            'paginated_matching_entries': matching_entries,
            'total_matches': total_matches,
            'site_url': settings.SITE_URL,
            'debug': request.GET.get('debug'),
            'query_seconds': (query_end-query_start).total_seconds(),
        })

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return redirect('searcher:index')

        return redirect("{}?query={}".format(reverse('searcher:index'), form.data.get('query')))
