from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    # Courses and Staff Admin (fold)
    url(r'^list_courses/$',
       views.courses,
       name='quiz_courses'
    ),
    # Admin begin
    url(r'^administrative/$', 
        views.administrative, 
        name='quiz_admin'
    ),
    url(r'^administrative/create_course/$', 
        views.create_course, 
        name='create_course'
    ),
    url(r'^administrative/add_staff_member/$', 
        views.add_staff_member, 
        name='add_staff_member'
    ),
    url(r'^administrative/see_marks/$', 
        views.see_marks, 
        name='see_marks'
    ),
    url(r'^administrative/(?P<course_pk>\d+)/see_all_marks/$', 
        views.see_all_marks, 
        name='see_all_marks'
    ),
    url(r'^administrative/(?P<course_pk>\d+)/download_all_marks/$', 
        views.download_all_marks, 
        name='download_all_marks'
    ),
    url(r'^administrative/add_students/$', 
        views.add_students, 
        name='add_students'
    ),
    url(r'^course_search/$', 
        views.course_search, 
        name='course_search'
    ),
    url(r'^enroll_course/$', 
        views.enroll_course, 
        name='enroll_course'
    ),
    url(r'^delete/(?P<objectStr>.+)/(?P<pk>\d+)$', 
        views.delete_item, 
        name='delete_item'
    ),

    # Courses and Staff Admin (end)

    # Quizzes and Quiz Admin (fold)
    url(r'^course/(?P<course_pk>\d+)/add_new_quiz', 
        views.new_quiz, 
        name='new_quiz'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/edit_quiz/$', 
        views.edit_quiz, 
        name='edit_quiz'
    ),
    url(r'^course/(?P<course_pk>\d+)/list_quizzes/$',
       views.list_quizzes,
       name='list_quizzes'
    ),
    url(r'^course/(?P<course_pk>\d+)/start/(?P<quiz_pk>\d+)/$',
       views.start_quiz,
       name='start_quiz'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/display_question/(?P<sqr_pk>\d+)/$',
       views.display_question,
       name='display_question'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/display_question/(?P<sqr_pk>\d+)/(?P<submit>\w+)$',
       views.display_question,
       name='display_question'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/admin/$',
       views.quiz_admin,
       name='quiz_admin'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/edit_question/$',
       views.edit_quiz_question,
       name='edit_quiz_question'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/edit_question/(?P<mq_pk>\d+)/$',
       views.edit_quiz_question,
       name='edit_quiz_question'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/edit_question/(?P<mq_pk>\d+)/edit_choices/$',
       views.edit_choices,
       name='edit_choices'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/edit_question/(?P<mq_pk>\d+)/test$',
       views.test_quiz_question,
       name='test_quiz_question'
    ),
    url(r'^course/(?P<course_pk>\d+)/quiz/(?P<quiz_pk>\d+)/details/(?P<sqr_pk>\d+)/$',
       views.quiz_details,
       name='quiz_details'
    ),
    url(r'^course/(?P<course_pk>\d+)/search_students/$',
       views.search_students,
       name='search_students'
    ),
    url(r'^course/(?P<course_pk>\d+)/search_results/(?P<user_pk>\d+)/$',
       views.student_results,
       name='student_results'
    ),

    # Quizzes and Quiz Admin (end)
]
