from django import template
from quizzes.models import *
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.conf import settings

import re

register = template.Library()

@register.inclusion_tag('quizzes/navbar.html', takes_context = True)
def navbar_inclusion_tag(context):
    return {
            'request': context.request, 
            'site_name': settings.SITE_NAME,
            'logout_page': settings.LOGOUT_REDIRECT_URL,}

@register.simple_tag
def check_active(request, view_name):
    return
#    if not request:
#        return ''
#    try:
#        if view_name in resolve(request.path_info).url_name:
#            return 'active'
#        else:
#            return ''
#    except Resolver404:
#        return ''

@register.simple_tag
def to_percent(num, den):
    return round(100*num/den)

@register.simple_tag
def score_div(num, den):
    #div_str = '<div class="{cl}" style="width: {widthperc}%; margin-left:30px">{perc}% <small>({num_votes} votes)</small></div>'
    div_str = '<div class="{cl}" style="width: {widthperc}%; margin-left:30px"></div>{perc}% <small>({num_votes} votes)</small>'


    if den == 0:
        ret_str = div_str.format(cl="zerobar", widthperc=100, perc="No votes", num_votes="No")
    else:
        percent = round(100*num/den)
        if percent==0:
            ret_str = div_str.format(cl="zerobar", widthperc=100, perc=percent, num_votes=num)
        else:
            ret_str = div_str.format(cl="bar", widthperc=percent, perc=percent, num_votes=num)

    return mark_safe(ret_str)

def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False;

@register.filter
def get_range(value):
    "Generates a range for numeric for loops"
    return range(value)


@register.simple_tag
def mathify_choice(choice):
    """ Takes a choice list from a MarkedQuestion element and outputs the math friendly html. Currently only
        supports integers.
        Input: choice (list of strings) -
        Output: KaTeX renderable HTML.
    """
    mathstring = '\(\{'
    for element in choice.replace(' ', '').split(';'):
        if is_integer(element):
            mathstring += element + ','
        else:
            try:
                match1 = re.match(r'[rR]and\((-?\d+),(-?\d+)\)',element)
                match2 = re.match(r'uni\((-?\d*\.?\d+),(-?\d*\.?\d+),(\d+)\)',element)

                if match1:
                    field = '\mathbb Z'
                    lower,upper = match1.groups(0)
                    acc = ''
                elif match2:
                    field = '\mathbb R'
                    lower,upper,acc = match2.groups(0)
                else:
                    field = 'Un'
                    lower = ''
                    upper = ''
                    acc   = ''

            #    lower,upper = element[1:].split(',')
            #    integer = '\mathbb Z'

            #    if element[0].istitle():
            #        integer +='^*'

                mathstring += ' {field}_{{ {acc} }}({low},{upp}), '.format(field=field, low=lower, upp=upper, acc=acc)

            except ValueError as error:
                print(error)
                return ''

    # Remove the final unnecessary ','
    mathstring = mathstring[0:-1]
    mathstring += '\}\)'

    return format_html('<label class="mathrender">{}</label>', mathstring)

