from django import template
import json
register = template.Library()

@register.filter(name="toJson")
def toJson(data):
    return json.dumps(data)


@register.filter(name='getValue')
def getValue(dic, key):
    return dic[key]