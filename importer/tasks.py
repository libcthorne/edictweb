import re
from datetime import datetime
from xml.etree.ElementTree import iterparse

from django.db import transaction

from importer import const
from importer.models import (
    db_conn,
    DictionaryEntry,
    DictionaryImportRequest,
    InvertedIndexEntry,
    PendingDictionaryImportRequest,
)
from indexer import tasks as indexer_tasks

def get_pending_import_request_id():
    return PendingDictionaryImportRequest.objects.first().import_request_id

def process_import_request(import_request_id):
    set_collection_ownership(import_request_id)

    _mark_import_request_as_started(import_request_id)

    print("[Request %d] Removing pending indexer tasks" % import_request_id)
    indexer_tasks.cleanup_tasks()

    print("[Request %d] Deleting existing dictionary entries" % import_request_id)
    _remove_existing_entries()

    print("[Request %d] Starting dictionary file import" % import_request_id)
    import_start_time = datetime.now()
    saved_entries_count = _save_dictionary_entries(import_request_id)

    _mark_import_request_as_completed(import_request_id)

    import_finish_time = datetime.now()
    import_duration = import_finish_time - import_start_time
    print("[Request %d] Finished dictionary file import in (entries: %d, duration: %s)" % (
        import_request_id,
        saved_entries_count,
        import_duration,
    ))

def cancel_pending_import():
    with transaction.atomic():
        pending_import_request = PendingDictionaryImportRequest.objects.select_for_update().first()

        if pending_import_request.import_request_id:
            set_collection_ownership(0)
            indexer_tasks.cleanup_tasks()
            pending_import_request.import_request.delete()

def set_collection_ownership(import_request_id):
    db_conn.dictionary_index.command(
        "collMod", "dictionary_entry",
        validator={"import_request_id": {"$eq": import_request_id}}
    )
    db_conn.dictionary_index.command(
        "collMod", "inverted_index_entry",
        validator={"import_request_id": {"$eq": import_request_id}}
    )

def _mark_import_request_as_started(import_request_id):
    import_request = DictionaryImportRequest.objects.get(id=import_request_id)
    import_request.started = True
    import_request.save()

def _mark_import_request_as_completed(import_request_id):
    import_request = DictionaryImportRequest.objects.get(id=import_request_id)
    import_request.completed = True
    import_request.save()

    pending_import_request = PendingDictionaryImportRequest.objects.get(import_request=import_request)
    pending_import_request.import_request = None
    pending_import_request.save()

def _remove_existing_entries():
    DictionaryEntry.objects.all().delete()
    InvertedIndexEntry.objects.all().delete()

def _parse_frequency_rank(priority_elems):
    min_rank = None

    for priority_elem in priority_elems:
        priority_str = priority_elem.text
        rank = None

        if priority_str == "ichi1":
            rank = 10
        elif priority_str == "ichi2":
            rank = 20
        elif const.FREQUENCY_STRING_REGEX.search(priority_str):
            rank = int(priority_str[2:])

        if rank is not None:
            if min_rank is not None:
                min_rank = min(rank, min_rank)
            else:
                min_rank = rank

    if min_rank is not None:
        return min(min_rank, const.MAX_FREQUENCY_RANK)

def _parse_entry(elem):
    sequence_number = int(elem.find("ent_seq").text)
    en_text = ""
    jp_text = ""
    meta_text = ""
    min_frequency_rank = None

    kanji_elems = elem.findall("k_ele")
    for kanji_elem in kanji_elems:
        kanji = kanji_elem.find("keb").text
        jp_text += kanji
        jp_text += const.JP_TEXT_DESCRIPTION_SEPARATOR

        frequency_rank = _parse_frequency_rank(kanji_elem.findall("ke_pri"))
        if frequency_rank is not None:
            if min_frequency_rank is not None:
                min_frequency_rank = min(frequency_rank, min_frequency_rank)
            else:
                min_frequency_rank = frequency_rank

    reading_elems = elem.findall("r_ele")
    for index, reading_elem in enumerate(reading_elems):
        reading = reading_elem.find("reb").text
        jp_text += reading
        if index+1 < len(reading_elems):
            jp_text += const.JP_TEXT_DESCRIPTION_SEPARATOR

        frequency_rank = _parse_frequency_rank(reading_elem.findall("re_pri"))
        if frequency_rank is not None:
            if min_frequency_rank is not None:
                min_frequency_rank = min(frequency_rank, min_frequency_rank)
            else:
                min_frequency_rank = frequency_rank

    sense_elems = elem.findall("sense")
    for sense_index, sense_elem in enumerate(sense_elems):
        pos_elems = sense_elem.findall("pos")
        for pos_index, pos_elem in enumerate(pos_elems):
            meta_text += pos_elem.text
            if pos_index+1 < len(pos_elems):
                meta_text += const.META_TEXT_SEPARATOR

        gloss_elems = sense_elem.findall("gloss")
        for gloss_index, gloss_elem in enumerate(gloss_elems):
            en_text += gloss_elem.text
            if gloss_index+1 < len(gloss_elems):
                en_text += const.EN_TEXT_DESCRIPTION_SEPARATOR

        if sense_index+1 < len(sense_elems):
            en_text += const.EN_TEXT_DESCRIPTION_SEPARATOR

    return sequence_number, en_text, jp_text, meta_text, min_frequency_rank

def _save_dictionary_entries(import_request_id):
    context = iterparse(const.DICTIONARY_FILE, events=("start", "end"))
    context = iter(context)
    _, root = next(context)
    entry_index = 0
    for event, elem in context:
        if event == "start":
            continue

        if elem.tag != "entry":
            continue

        (
            sequence_number,
            en_text,
            jp_text,
            meta_text,
            min_frequency_rank,
        ) = _parse_entry(elem)

        # Create and save new entry
        entry = DictionaryEntry(
            jp_text=jp_text,
            en_text=en_text,
            meta_text=meta_text,
            sequence_number=sequence_number,
            frequency_rank=min_frequency_rank,
            common=min_frequency_rank is not None,
            import_request_id=import_request_id,
        )
        entry.save()
        print("[Request %d] Saved %d entry lines" % (import_request_id, entry_index+1))

        # Add to index
        indexer_tasks.index_dictionary_entry_by_id.apply_async(
            args=(str(entry.id),)
        )

        # Log progress
        print("[Request %d] Progress: %d entries saved" % (import_request_id, entry_index+1))

        # Remove entry from root tree to keep memory usage low
        root.clear()

        entry_index += 1

    return entry_index
