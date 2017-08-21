from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.html import mark_safe, format_html
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Max, Q, F

from .models import *
from .forms import *
from guardian.shortcuts import get_objects_for_user
import json
import csv

def staff_required(login_url=settings.LOGIN_URL):
    return user_passes_test(lambda u:u.is_staff, login_url=login_url)


@staff_required()
def delete_item(request, objectStr, pk):
    """ Generically used to delete items
    """
    if request.user.is_staff:
        # Depending on which item is set, we return different pages
        if objectStr == "pollquestion":
            theObj = get_object_or_404(
                    PollQuestion.objects.select_related('poll', 'poll__course'),
                    pk = pk)
            description = "PollQuestion {}".format(pk)
            poll = theObj.poll
            course = theObj.poll.course
            if request.user.has_perm('polls.can_edit_poll', course):
                return_view = redirect(reverse(
                        'poll_admin',  
                        kwargs={
                            'course_pk': course.pk,
                            'poll_pk': poll.pk,
                        }))
            else:
                raise HttpResponseForbidden(
                    "You are not authorized to delete that object")

        else:
            return HttpResponse('<h1>Invalid Object Type</h1>')

        if request.method == "POST":
            theObj.delete()
            return return_view
        else:
            return render(
                request, 
                'polls/delete_item.html', 
                {'object': theObj, 
                 'type' : objectStr,
                 'description': description,
                 'return_url': return_view.url
                 }
            )
    else:
        return HttpResponseForbidden()

@login_required
def home(request):
    return render(request, 'polls/home.html')

@login_required
def courses(request):
    membership,_ = UserMembership.objects.get_or_create(
                    user=request.user)
    courses = membership.courses.all()
    return render(
        request, 
        'polls/courses.html', 
        {'courses' : courses} )

@login_required
def administrative(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Not a valid User")
    else:
        return render(
            request,
            'polls/administration.html')

@login_required
def list_polls(request, course_pk):
    course = Course.objects.get(pk=course_pk)
    polls = Poll.objects.filter(course=course)

    return render(
        request, 
        'polls/list_polls.html', 
        {'course_pk': course.pk, 
            'polls' : polls,
         'course'   : course,})

@staff_required()
def new_poll(request, course_pk):
    if request.method == "POST":
        form = PollForm(request.POST)
        if form.is_valid():
            course = Course.objects.get(pk=course_pk)
            poll = form.save(commit=False)
            poll.course = course
            poll.save()

            return redirect('list_polls', course_pk=course_pk)
    else:
        form = PollForm()

    return render(
            request, 
            'polls/edit_announcement.html', 
            {'form' : form})

@login_required
def list_pollquestions(request, course_pk, poll_pk):
    """ Lists the poll questions. Course_pk is entered for the sake of url
        consistency, but is not necessary
    """
    poll = get_object_or_404(Poll, pk=poll_pk)
    questions = poll.questions.order_by('position')

    return render(
            request, 
            'polls/list_pollquestions.html', 
            {
                'questions': questions, 
                'poll': poll,
                'course_pk': course_pk,
            })

## ----------------- Poll Admin ----------------------- ##

# Only handles rendering the poll admin page. AJAX requests handled by other views
@staff_required()
def poll_admin(request, course_pk, poll_pk):
    """ Used by poll administrator to add/edit/delete questions, as well as to
    active the polls for access to student. course_pk is unnecessary.
    """
    poll = get_object_or_404(Poll, pk=poll_pk)
    questions = poll.questions.all().order_by('position')
    course = Course.objects.get(pk=course_pk)

    if not request.user.has_perm('can_see_poll_admin', poll.course):
        return HttpResponseForbidden("Insufficient Privileges")

    return render(
            request, 
            'polls/poll_admin.html', 
            {
                'poll': poll, 
                'questions': questions,
                'course': course,
                'poll_pk': poll_pk,
                'url_prepend': settings.URL_PREPEND,
            })

@staff_required()
def change_question_order(request):
    """ AJAX handler for poll_admin page to change question order. 
        request.POST should have elements action, pk
    """

    data   = request.POST
    pk     = int(data['pk'])
    action = data['action']

    question = get_object_or_404(PollQuestion, pk=pk)
    ret_flag = question.move_position(action)

    if (ret_flag < 0) :
        response_data = {'response': 'No movement of questions'}
    else:
        response_data = {'response': 'Question successfully moved'}

    return HttpResponse(json.dumps(response_data))

## ----------------- Poll Admin ----------------------- ##


@staff_required()
def new_pollquestion(request, course_pk, poll_pk, question_pk=None):
    """ Creates a new poll question. course_pk is just along for the ride
    """
    # To facilitate question + choice at the same time, we must instantiate the
    # question before hand. This will also make editing a question easy in the
    # future
    poll = get_object_or_404(Poll, pk=poll_pk)

    if not request.user.has_perm('can_edit_poll', poll.course):
        return HttpResponseForbidden("Unauthorized access")

    # If a question is created for the first time, we must instantiate it so that
    # our choices have somewhere to point. If it already exists, retrieve it
    if question_pk is None:
        # With positioning, we need to determine the largest current position.
        cur_pos = PollQuestion.objects.filter(poll=poll).aggregate(Max('position'))

        if cur_pos['position__max'] is None:
            question = PollQuestion(poll=poll, position = 0)
        else:
            question = PollQuestion(poll=poll, position = cur_pos['position__max'] + 1)
        question.save()
    else:
        question = get_object_or_404(PollQuestion, pk=question_pk)

        if (request.method == "POST") and ('del' in request.POST):
            # User has left the page without submitting the form. So delete the question
            question.delete()
            data_response = {'response': 'Object successfully deleted'}
            return HttpResponse(json.dumps(data_response))

    if request.method == "POST":
        try:
            data = request.POST
            numChoices    = int(data['num-choice'])
            question.text = data['question']

            question.save()

            # Iterate through the choices. Ignore empty choices and otherwise create
            # database element. Note that numChoice is absolute (starts at 1), while 
            # the id's for input names start at 0
            for myit in range(0, numChoices):
                id_name = "new_" + str(myit)
                c_text = data[id_name]

                if c_text != '':
                    choice = PollChoice(question=question, text=c_text, cur_poll=question.num_poll)
                    choice.save()

            return redirect(reverse(
                'poll_admin', 
                kwargs = {'poll_pk':poll_pk,
                          'course_pk': course_pk
                         }))
        except:
            raise Http404('Something went wrong!')

        return redirect(reverse(
                'poll_admin', 
                kwargs = {'poll_pk':poll_pk,
                          'course_pk': course_pk
                         }))

    else:
        return render(request, 
                'polls/new_pollquestion.html',  
                {'question' : question,
                 'poll_pk'  : poll_pk,
                 'course_pk': course_pk})

# Cannot just abuse new_question because we need to handle choices differently
@staff_required()
def edit_pollquestion(request, course_pk, poll_pk, question_pk):
    """ Creates a form to allow the poll adminstrator to change a question. As
        with everything, course_pk is just along for the ride
    """
    question = get_object_or_404(PollQuestion, pk=question_pk)
    choices = question.choices.filter(cur_poll=question.num_poll)

    # On form submission, update everything
    if request.method == "POST":
        form_data = request.POST
        # Note here that iteritems for python 2.x and items for python 3
        for field, data in form_data.items():
            if field == 'question':
                question.text = form_data[field]
                question.save()
            # 'old' indicates a previous existing choice
            elif 'old' in field:
                pkstring  = field.split('_')
                choice_pk = int(pkstring[-1])

                choice = get_object_or_404(PollChoice, pk=choice_pk)
                choice.text = form_data[field]
                if choice.text == '':
                    choice.delete()
                else:
                    choice.save()
            # 'choice' indicates a new choice that was added
            elif 'new' in field:
                c_text = form_data[field]

                choice = PollChoice(question=question, text=c_text, cur_poll=question.num_poll)
                choice.save()

        return redirect(reverse(
                'poll_admin', 
                kwargs={
                    'poll_pk':question.poll.pk,
                    'course_pk': course_pk,
                    'poll_pk': poll_pk,
                }))
    else:
        return render(
                request, 
                'polls/new_pollquestion.html', 
                {
                    'question': question, 
                    'choices': choices, 
                    'edit': True,
                    'course_pk': course_pk,
                    'poll_pk': poll_pk})


# AJAX view for making a question live
@csrf_protect
def make_live(request):
    question = get_object_or_404(PollQuestion, pk=int(request.POST['question']))
    question.live = (request.POST['live']=='true');
    question.save()

    response_data = {'response': 'Question Visible: ' + str(question.live)}

    return HttpResponse(json.dumps(response_data))

# AJAX view for an administrator to start/stop/reset a question
@csrf_protect
def live_question(request):
    """
        AJAX view for poll-admin page. request.POST should have a field called 'status' which
        describes which button was hit. Can be one of
            'start'  - make a question live and open voting
            'stop'   - close voting, display results, and reset
            'endall' - removes questions from the poll page
    """
    if request.user.is_staff:
        data = request.POST
        question_pk = int(data['questionpk'])
        status   = data['action']

        question = get_object_or_404(PollQuestion, pk = question_pk)

        if status == 'endall':
            # Make sure this only kills the poll questsions for this course
            PollQuestion.objects.filter(
                    visible=True,
                    poll__course=question.poll.course
                    ).update(
                        visible=False, 
                        can_vote=False)
            response_data = {'response': 'Polling has ended'}
            return HttpResponse(json.dumps(response_data))

        # The PollQuestion model has built in functions for this. But we have to make sure
        # that this is the only live question on start.
        #
        # As of June 15, 2015, moved reset() to stop.
        if status == 'start':
            # It is possible that the administrator accidentally hit the start button again.
            # We check to see if this is the case, and return an error message if so.
            if question.can_vote:
                response_data = {'response': 'This question is already active'}
            else: 
                # On 'start' we reset the poll. However, to avoid saving a bunch of empty polls
                # we first check to see if any votes have been cast.
                choices  = question.choices.filter(cur_poll=question.num_poll)
                num_votes = sum(choices.values_list('num_votes', flat=True))

                response_data = {'response': 'Question pushed to live page'}
                if num_votes != 0:
                    pk_map = question.reset()
                    response_data['pkMap'] = pk_map
                
                # The model now takes care of this. Also, need to update for
                # current course if reimplemented
                # PollQuestion.objects.filter(visible=True).update(visible=False, can_vote=False)
                question.start()
        elif status == 'stop':
            if not question.can_vote:
                response_data = {'response': 'This question is not live.'}
            elif not question.visible:
                response_data = {'response': 'That question is not visible'}
            else:
                question.stop()
                response_data = {'response': 'Question stopped. Displaying results.'}
#        elif status == 'reset':
#            if not question.visible:
#                response_data = {'response': 'That question is not visible'}
#            else:
#                pk_map = question.reset()
#                response_data = {'response': 'Data saved. Press start to reopen.', 'pkMap': pk_map}
    else:
        response_data = {'response': 'You are not authorized to make this POST'}

    return HttpResponse(json.dumps(response_data))

# Server is only ever in one of three states:
# 1. Nothing is happening
# 2. Question is displayed and voting
# 3. Question is display with results of most recent vote
# Depending on the states, we render a different page
@login_required
def live_poll(request, course_pk):
    # See if a question has been opened by an administrator. This is course
    # specific
    course = get_object_or_404(Course, pk=course_pk)

    try: 
        question = PollQuestion.objects.get(
                visible=True,
                poll__course=course #Only this course
                )
        choices  = question.choices.filter(cur_poll=question.num_poll)
        num_votes = sum(choices.values_list('num_votes', flat=True))

        # Used to identify if a change has occured. For example
        # 15T = Question 15 is live and can be voted on
        # 15F = Question 15 is visible but voting is over
        # -1  = (set later) no question
        state = str(question.pk)+"-"+str(question.can_vote)
        return render(
                request, 
                'polls/live_poll.html', 
                {
                    'question': question, 
                    'choices': choices, 
                    'state': state, 
                    'votes':num_votes,
                    'course': course,
                    'url_prepend': settings.URL_PREPEND,
                })

    # If no question is currently live, we do nothing
    except PollQuestion.DoesNotExist:
        state = "-1"
        return render(
                request, 
                'polls/live_poll.html', 
                {
                    'state': state,
                    'course': course,
                    'url_prepend': settings.URL_PREPEND,
                })
    except PollQuestion.MultipleObjectsReturned:
    # Somehow multiple questions are visible. Shut them all down.
        PollQuestion.objects.filter(
                visible=True,
                poll__course=course #Only this course
                ).update(
                    visible=False,
                    can_vote=False)
        state = "-1"
        return render(
                request, 
                'polls/live_poll.html', 
                {
                    'state': state,
                    'course': course,
                    'url_prepend': settings.URL_PREPEND,
                })

@login_required
def query_live(request):
    """ Function for handling AJAX 
    """
   
    # Votes are POSTed, status changes are done via GET
    # [Future] Currently user can vote as many times as they like by refreshing. May need
    # to create a db-model to track voting.
    if request.method == "POST": # Vote submitted
        # POST will send choicepk as field 'pk'
        choicepk = int(request.POST['pk'])
        choice   = get_object_or_404(PollChoice, pk=choicepk)

        # Get or create a StudentVote object
        # In particular, check to see if the student has voted in the current poll.
        # There is the potential here for race conditions, so we place the code
        # in an atomic manager, and use the select_for_update method to lock the
        # row
        with transaction.atomic():
            try:
                svote, created = (StudentVote.objects.select_for_update()
                                    .get_or_create(
                                        student=request.user, 
                                        cur_poll = choice.cur_poll, 
                                        question=choice.question
                                    )
                                 )
            except IntegrityError as dberror:
                return HttpResponse('<h2>You have attempted to submit multiple votes</h2>')

            if created: # First vote
                svote.choice = choice;
                svote.add_choice(choice)
            else: # Revoting, so change the vote
                if svote.vote != choice:
                    svote.change_vote(choice)

            response_data = {'status': 'success'}
    else: # GET request, so checking on the status of the page. This is
          # inefficient, as we need to query the db every time this request is
          # made. This whole thing will be rewritten for websocket interface
        course_pk = int(request.GET['course_pk'])
        course = Course.objects.get(pk=course_pk)
        try: 
            question = PollQuestion.objects.get(
                    poll__course=course,
                    visible=True
                    )
            state = str(question.pk)+"-"+str(question.can_vote)

            response_data = {'state': state}

            # If the user is staff, return the number of votes as well
            if request.user.is_staff:
                choices  = question.choices.filter(cur_poll=question.num_poll)
                num_votes = sum(choices.values_list('num_votes', flat=True))
                response_data['numVotes'] = num_votes
                for choice in choices:
                    field = str(choice.pk)+"-votes"
                    num_votes = str(choice.num_votes)
                    response_data[field]=num_votes

        except Exception as e:
            response_data = {'state': "-1"}

    return HttpResponse(json.dumps(response_data))


@staff_required()
def poll_history(request, course_pk, poll_pk, question_pk, poll_num=None):
    """ A view handler for a staff member to view poll question histories.
        course_pk and poll_pk are along for the ride
        Input: questionpk - an integer corresponding to the primary key for the pollquestion
               poll_num   - a number corresponding to the value of the poll. -1 indicates all polls
    """

    question = get_object_or_404(PollQuestion, pk=question_pk)

#    try:
    data = request.GET
    return_data = {}
    if poll_num == "-1":
        choices = question.choices.all()
    elif poll_num is not None:
        choices = question.choices.filter(cur_poll=int(poll_num))
        num_votes = sum(choices.values_list('num_votes', flat=True))
        return_data['votes']    = num_votes
    else:
        choices = question.choices.filter(cur_poll=question.num_poll)
        num_votes = sum(choices.values_list('num_votes', flat=True))
        return_data['votes']    = num_votes

    return_data['question'] = question
    return_data['choices']  = choices
    return_data['poll_num'] = int(poll_num)

    return_data['course_pk'] = course_pk
    return_data['poll_pk'] = poll_pk
    
    return render(
            request, 
            'polls/poll_history.html', 
            return_data)

#    except Exception as e:
#        raise Http404('An error occured in processing your request. Exception: ' + str(e))

@staff_required()
def who_voted(request, course_pk, poll_pk, question_pk, poll_num):
    """ Post the usernames of the students who voted in the given question, and how they voted
        Input: questionpk (integer) - Number corresponding to the question primary key
                 poll_num (integer) - The current poll number
        Output: HttpResponse
        Context: List of tuples (username, vote_id)
    """

    question = get_object_or_404(PollQuestion, pk=question_pk)
    choices  = question.choices.filter(cur_poll=int(poll_num))

    student_votes = StudentVote.objects.filter(question=question, cur_poll=poll_num).values_list('student__username', 'vote__pk')

#    iterators = []
#    # For each choice correspond to the question, generate the list of students who voted on that question.
#    # The for loop creates an iterator, then we chain together the iterators at the end.
#    for choice in choices:
#        student_voters = choice.student_set.all().values_list('username', flat=True)
#        iterators.append(itertools.product(student_voters, [choice.pk]))
#
#    student_list = itertools.chain.from_iterable(iterators)

    return render(request, 'polls/who_voted.html', 
            {
                'list': student_votes,
            })

# ----------------- (fold) History ----------------------- #

# --------- Course Administration ------- #

def generate_redirect_string(name, url):
    """ Shortcut for generating the redirect html to be inserted into
    success.html
    """
    return "<a href={}>Return to {}</a>".format(url,name)

def create_course(request):
    """ View for generating and handling the create course form. This form asks
    for the name of the course, and the default administrator. The view must
    handle setting the administrator.
    """
    if not request.user.is_superuser:
        raise HttpResponseForbidden("You are not authorized to create a course")

    if request.method == "POST": # Form returned filled in
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            # If a default admin has been specified, add them
            username = request.POST['default_admin']
            success_string = "Course {} successfully created".format(
                    course.name )
            if username:
                course.add_admin(username)
                success_string += "<br>User {} added as default admin".format(
                        username)
            redirect_string = generate_redirect_string(
                    'Administration', reverse('poll_admin') )

            return render(request,
                    'polls/success.html',
                    { 'success_string': success_string,
                      'redirect_string' : redirect_string,
                    }
                )
    else: # request method is GET, so seeing page for the first time
        form = CourseForm()

        return render(request, 'polls/generic_form.html', 
                {'form': form,
                 'header': "Create Course"
                }
            )

def add_staff_member(request):
    """ Add staff members to a course """
    # Populate the form with list of courses 
    courses = get_objects_for_user(request.user, 'polls.can_edit_poll')
    if request.method == "POST":
        form = StaffForm(request.POST)
        course_pk = int(request.POST['course'])
        username  = request.POST['username']
        is_admin = 'admin' in request.POST

        course = Course.objects.get(pk=course_pk)
        course.add_admin(username, staff=not is_admin)

        redirect_string = generate_redirect_string(
            'Administrative', reverse('poll_admin') )
        success_string = ("User {} successfully added to course {} "
           "with {} privileges").format(
               username, course.name, "admin" if is_admin else "staff")

        return render(request, 'polls/success.html',
            { 'success_string': success_string,
              'redirect_string': redirect_string,
            }
        )
    else:
        form = StaffForm(queryset=courses)
        return render(request, 'polls/generic_form.html',
            { 'form': form,
              'header': "Add Staff Member",
            }
        )

def add_students(request):
    # Populate the form with list of courses 
    courses = get_objects_for_user(request.user, 'polls.can_edit_poll')
    sidenote = ("Upload a csv file whose rows are the UTORid's of the "
        "students you wish to add to this course")
    if request.method == "POST":
        form = AddStudentsForm(request.POST, request.FILES, queryset=courses)

        if form.is_valid():
            # Get the course
            course_pk = int(request.POST['course'])
            course = Course.objects.get(pk=course_pk)
            # Save the file to make it easier to read from later
            csv_file = form.save()

            # Read through the CSV file 
            with open(csv_file.doc_file.path, 'rt') as the_file:
                for row in csv.reader(the_file):
                    username = row[0]
                    user, _ = User.objects.get_or_create(username=username)
                    # Get the membership and add this course to that
                    membership, _ = UserMembership.objects.get_or_create(user=user)
                    membership.courses.add(course)

            redirect_string = generate_redirect_string(
                'Administrative', reverse('poll_admin') )
            success_string = "Students successfully added to course {} ".format(
                   course.name)

            return render(request, 'polls/success.html',
                { 'success_string': success_string,
                  'redirect_string': redirect_string,
                }
            )

        return render(request, 'polls/generic_form.html',
            { 'form': form,
              'header': "Add Students to Course",
              'sidenote': sidenote,
            }
        )
    else:
        form = AddStudentsForm(queryset=courses)
        return render(request, 'polls/generic_form.html',
            { 'form': form,
              'header': "Add Students to Course",
              'sidenote': sidenote,
            }
        )

@login_required
def course_search(request):
    """ AJAX view for searching for open enrollment courses. GET should contain
    'query' 
    """
    if request.method == "GET":
        query = request.GET['query']
        
        courses = Course.objects.filter(
            open_enrollment=True, name__contains=query)[:10]
        membership = UserMembership.objects.get(user=request.user)

        return render(request, 'polls/course_search.html',
            { 'courses': courses,
              'membership': membership
            }
        )

@login_required
def enroll_course(request):
    """ AJAX view for enrolling a student in an open enrollment course
    """

    if request.method == "POST":
        course_pk = int(request.POST['course_pk'])
        course = get_object_or_404(Course, pk=course_pk)
        if course.open_enrollment:
            membership, _ = UserMembership.objects.get_or_create(user=request.user)
            membership.courses.add(course)
            response_data = {'response': 'success'}
        else:
            response_data = {'response': 'Course does not permit open enrollment'}
    else:
        response_data = {'response': 'Invalid HTTP request'}

    return HttpResponse(json.dumps(response_data))
