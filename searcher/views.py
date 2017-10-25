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

        # Find relevant entries
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

        # Paginate results
        paginator = Paginator(matching_entries, per_page=20)

        page = request.GET.get('page')
        try:
            matching_entries = paginator.page(page)
        except PageNotAnInteger:
            matching_entries = paginator.page(1)
        except EmptyPage:
            matching_entries = paginator.page(paginator.num_pages)

        total_matches = paginator.count

        if query:
            # Highlight text match positions

            match_positions = InvertedIndexEntry.objects.\
                              filter(index_word__word__in=normalized_words).\
                              filter(dictionary_entry__in=matching_entries).\
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
                matching_entry.edict_data_highlighted = []
                prev_match_end = 0

                for match_position in match_positions_for_entry[matching_entry.id]:
                    match_start = match_position['start_position']
                    match_end = match_position['end_position']

                    # Everything from last match to current match start is not highlighted
                    matching_entry.edict_data_highlighted.append((
                        False,
                        matching_entry.edict_data[prev_match_end:match_start],
                    ))
                    # Current match is highlighted
                    matching_entry.edict_data_highlighted.append((
                        True,
                        matching_entry.edict_data[match_start:match_end],
                    ))

                    prev_match_end = match_end

                # Any remaining text after last match is not highlighted
                data_end = len(matching_entry.edict_data)
                if prev_match_end < data_end:
                    matching_entry.edict_data_highlighted.append((
                        False,
                        matching_entry.edict_data[prev_match_end:data_end],
                    ))

                print(matching_entry.edict_data_highlighted)

        return render(request, 'searcher/index.html', {
            'form': form,
            'entries': matching_entries,
            'showing_matches': bool(query),
            'total_matches': total_matches,
        })

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return redirect('searcher:index')

        return redirect("{}?query={}".format(reverse('searcher:index'), form.data.get('query')))
