from .models import DictionaryImportRequest

def start_dictionary_import():
    request = DictionaryImportRequest()
    request.save()
    return request
