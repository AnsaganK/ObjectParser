from django import template
import json

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