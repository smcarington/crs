from django import template
from polls.models import *
# Migration from 1.11 to 2.2
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.conf import settings

import re

register = template.Library()

@register.inclusion_tag('polls/navbar.html', takes_context = True)
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

@register.simple_tag
def total_votes(questionpk, cur_poll):
    # For the question with pk questionpk, and the choices with cur_poll, return the total votes
    q = PollQuestion.objects.get(pk=questionpk)
    choices = q.choices.filter(cur_poll=cur_poll)
    return sum(choices.values_list('num_votes', flat=True))

def is_integer(string):
    try:
        int(string)
        return True
    except ValueError:
        return False;

@register.filter
def filter_poll_choice(query_set, poll=None):
    if type(query_set) is PollQuestion:
        if poll is None:
            return query_set.choices.filter(cur_poll=query_set.num_poll).order_by('id')
        else:
            return query_set.choices.filter(cur_poll=poll).order_by('id')
    elif type(query_set) is PollChoice:
        return query_set.filter(cur_poll=poll)

@register.filter
def get_range(value):
    "Generates a range for numeric for loops"
    return range(value)

