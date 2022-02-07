import requests
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from constants import CLOUDFLARE_AUTH_EMAIL, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_AUTH_KEY
from parsing.models import CloudImage
from parsing.templatetags.parsing_tags import GROUPS


def show_form_errors(request, errors):
    for error in errors:
        messages.error(request, f'{error} {errors[error]}')


def get_paginator(request, queryset, count=12):
    paginator = Paginator(queryset, count)
    page = request.GET.get('page')
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)
    return queryset


def has_group(user, group_name):
    if not user.is_authenticated:
        return False
    group = user.groups.first()
    if not group:
        return False
    current_index = GROUPS[group.name]
    recommended_index = GROUPS[group_name]
    if current_index < recommended_index:
        return False
    return True


def save_image(image):
    url = f'https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/images/v1'
    headers = {
        'X-Auth-Email': CLOUDFLARE_AUTH_EMAIL,
        'X-Auth-Key': CLOUDFLARE_AUTH_KEY,
    }
    files = {
        'file': image
    }
    r = requests.post(url, files=files, headers=headers)
    if r.status_code == 200:
        response = r.json()
        print(response['success'])
        if response['success'] == True:
            cloud_image = CloudImage(image_id=response['result']['id'], image_response=response)
            cloud_image.save()
            return cloud_image
    return None


# Суммаризация Description

from itertools import combinations
import nltk
from nltk.tokenize import sent_tokenize, RegexpTokenizer
from nltk.stem.snowball import RussianStemmer
from nltk.stem.snowball import EnglishStemmer
import networkx as nx


def similarity(s1, s2):
    if not len(s1) or not len(s2):
        return 0.0
    return len(s1.intersection(s2)) / (1.0 * (len(s1) + len(s2)))


def textrank(text):
    sentences = sent_tokenize(text)
    tokenizer = RegexpTokenizer(r'\w+')
    lmtzr = EnglishStemmer()
    words = [set(lmtzr.stem(word) for word in tokenizer.tokenize(sentence.lower()))
             for sentence in sentences]
    pairs = combinations(range(len(sentences)), 2)
    scores = [(i, j, similarity(words[i], words[j])) for i, j in pairs]
    scores = filter(lambda x: x[2], scores)
    g = nx.Graph()
    g.add_weighted_edges_from(scores)
    pr = nx.pagerank(g)
    return sorted(((i, pr[i], s) for i, s in enumerate(sentences) if i in pr), key=lambda x: pr[x[0]], reverse=True)


def sumextract(text, n=5):
    tr = textrank(text)
    top_n = sorted(tr[:n])
    return ' '.join(x[2] for x in top_n)


# Уникализация текста
# import requests

API_URL = "https://api-inference.huggingface.co/models/tuner007/pegasus_paraphrase"
headers = {"Authorization": "Bearer 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"}


def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
    except:
        return None

def uniqueize_text(text):
    sentences = text.split('.')
    sentences = [i for i in sentences if len(i) > 2]
    unique_sentences = ''
    output = query({
        "inputs": sentences,
        "parameters": {
            'truncation': 'only_first'
        }
    })
    if output:
        try:
            for i in output:
                unique_sentences += str(i['generated_text']) + ' '
            return unique_sentences
        except:
            return text
    return text
