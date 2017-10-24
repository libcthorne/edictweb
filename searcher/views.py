from collections import defaultdict

from django.core.paginator import (
    EmptyPage,
    PageNotAnInteger,
    Paginator,
)
from django.db.models import (
    Count,
    F,
    IntegerField,
    Value,
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

from importer.models import (
    DictionaryEntry,
    InvertedIndexEntry,
    InvertedIndexWord,
)
from .forms import SearchForm

class SearchView(View):
    def get(self, request):
        form = SearchForm(request.GET)
        if not form.is_valid():
            return HttpResponseBadRequest("Invalid form data")

        query = InvertedIndexWord.normalize_query(form.cleaned_data['query'])
        if not query:
            matching_entries = DictionaryEntry.objects.all()
            matching_entries = matching_entries.\
                               annotate(num_matches=Value(0, IntegerField())).\
                               order_by('id')

        else:
            normalized_words = [InvertedIndexWord.normalize_word(word) for word in query.split(' ')]
            matching_entries = DictionaryEntry.objects.filter(invertedindexentry__index_word__word__in=normalized_words).\
                               annotate(num_matches=Count('id')).\
                               order_by('-num_matches', 'id')

            # Highlight text match positions

            match_positions = InvertedIndexEntry.objects.filter(index_word__word__in=normalized_words).\
                              order_by('dictionary_entry_id', 'start_position', 'end_position').\
                              annotate(word=F('index_word__word'))

            match_positions_for_entry = defaultdict(list)
            for match_position in match_positions:
                match_positions_for_entry[match_position.dictionary_entry_id].append({
                    'word': match_position.word,
                    'start_position': match_position.start_position,
                    'end_position': match_position.end_position,
                })

            for matching_entry in matching_entries:
                additional_offset = 0
                for match_position in match_positions_for_entry[matching_entry.id]:
                    match_start = match_position['start_position'] + additional_offset
                    match_end = match_position['end_position'] + additional_offset
                    matching_entry.edict_data = matching_entry.edict_data[:match_start] + \
                                                '**' + \
                                                match_position['word'] + \
                                                '**' + \
                                                matching_entry.edict_data[match_end:]
                    additional_offset += len('****')

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
