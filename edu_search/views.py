from django.shortcuts import render
from .ir_engine import search_tfidf, search_bm25, get_slotted_sentences
import os
import pickle

def search_view(request):
    query = request.GET.get('q', '')
    model = request.GET.get('model', 'bm25')
    results = []
    
    if query:
        if model == 'bm25':
            results = search_bm25(query)
        else:
            results = search_tfidf(query)
            
    context = {
        'query': query,
        'model': model,
        'results': results,
    }
    return render(request, 'edu_search/index.html', context)

def slots_view(request):
    sentences = get_slotted_sentences()
    return render(request, 'edu_search/slots.html', {'sentences': sentences})

# --- KARYERA AI MENTOR (Ko'chirilgan) ---
# Barcha NLP va klassifikatsiya logikasi Groq API (LLaMA) orqali hal qilinadi.
# Ushbu funksiyalar vaqtinchalik o'chirib qo'yildi.

def career_mentor(request):
    return render(request, 'edu_search/career_mentor.html', {
        'query': '', 
        'result': None,
        'token_counts': {},
        'frequencies': {},
        'domain_info': "Ushbu xizmat tez orada sun'iy intellektning yangi avlodi (LLaMA) ga o'tkaziladi."
    })

from django.http import HttpResponse

def download_nlp_report(request):
    return HttpResponse("Xizmat vaqtincha to'xtatilgan.")

def download_global_dataset(request):
    return HttpResponse("Xizmat vaqtincha to'xtatilgan.")

def dataset_analytics(request):
    return render(request, 'edu_search/analytics.html', {
        'query': '',
        'global_stats': {},
        'token_counts': {},
        'frequencies': {},
        'inverted_index': {}
    })

