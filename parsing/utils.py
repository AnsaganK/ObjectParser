import requests
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from constants import CLOUDFLARE_AUTH_EMAIL, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_AUTH_KEY
from parsing.models import CloudImage
from parsing.templatetags.parsing_tags import GROUPS


def show_form_errors(request, errors):
    for error in errors:
        messages.error(request, f'{error} {errors[error]}')


def get_paginator(request, queryset, count):
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
        if response['success'] == True:
            cloud_image = CloudImage(image_id=response['result']['id'], image_response=response)
            cloud_image.save()
            return cloud_image
    return None