import re

from django import template
import json

from django.db.models.functions import Length

register = template.Library()

GROUPS = {'Пользователь': 1,
          'Редактор': 2,
          'Администратор': 3,
          'Суперадминистратор': 4}


@register.filter(name="getRating")
def getRating(rating):
    stars = ''
    rating = int(rating)
    for i in range(rating):
        stars += '<span style="color:gold;"><i class="fa fa-star"></i></span>'
    for i in range(5 - rating):
        stars += '<span style="color:lightgrey;"><i class="fa fa-star"></i></span>'
    return stars


@register.filter(name="hasGroup")
def hasGroup(user, group_name):
    group = user.groups.first()
    if not group:
        return False
    current_index = GROUPS[group.name]
    recommended_index = GROUPS[group_name]
    if current_index < recommended_index:
        return False
    return True

@register.filter(name="toJson")
def toJson(data):
    return json.dumps(data)


@register.filter(name='getValue')
def getValue(dic, key):
    return dic[key]

@register.filter(name="toString")
def toString(variable):
    return str(variable)

@register.filter(name="isValue")
def isValue(value):
    if value:
        return value
    return ' - '

@register.filter(name="getImg")
def getImg(img):
    if img:
        return img.url
    return '/static/img/not_found.png'

@register.filter(name="getBaseImg")
def getBaseImg(query):
    if query:
        places = query.places
        try:
            first_place = places.first().place.first()
            if first_place.img:
                return first_place.img.url
        except:
            pass
    return '/static/img/not_found.png'

@register.filter(name="getMetaText")
def getMetaText(meta):
    if meta == ' - ':
        return meta
    pattern = r'(?<=content=")(.+?)(?=")'
    meta = re.search(pattern, meta)
    if meta:
        return meta.group()
    return ' - '


@register.filter(name="getMoreText")
def getMoreText(queries):
    if queries:
        queries = queries.exclude(text=None).exclude(text='').annotate(text_len=Length('text')).order_by('-text_len')
        return queries.first()
    return ''


@register.filter(name="isSite")
def isSite(site):
    if not site:
        return ' - '
    if site[:4] == 'http':
        return site
    else:
        return 'http://'+site

