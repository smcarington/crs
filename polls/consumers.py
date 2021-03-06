import re
import json
import logging
from django.shortcuts import render
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.db import transaction, IntegrityError
from django.template import loader
from .models import *

class PollAdminConsumer(WebsocketConsumer):

    def connect(self):
        """ Consumer for when an administrator access the poll-admin feature. 
            ws:://host/ws/{settings.URL_PREPEND}/query_live/{course_pk}/{poll_pk}/poll_admin. 
            Group: Admin-{course_pk}
            Adds course_pk and poll_pk to session data.
        """
        #message.channel_session['course_pk'] = course_pk
        #message.channel_session['poll_pk'] = poll_pk
        self.course_pk = self.scope['url_route']['kwargs']['course_pk']
        self.poll_pk= self.scope['url_route']['kwargs']['poll_pk']
        self.admin_group_name = f"Admin-{self.course_pk}"
        self.voter_group_name = f"Voter-{self.course_pk}"

        async_to_sync(self.channel_layer.group_add)(
            self.admin_group_name,
            self.channel_name
        )
        #Group('Admin-'+course_pk).add(message.reply_channel)
        #message.reply_channel.send({'accept': True})

        self.accept()

    def disconnect(self, close_code):
        """ Disconnecting from poll-admin.  Remove from the group
        """
        async_to_sync(self.channel_layer.group_discard)(
            self.admin_group_name,
            self.channel_name
        )
        #course_pk = message.channel_session['course_pk']
        #Group('Admin'+course_pk).discard(message.reply_channel)

    # Attached to websocket.message
    def receive(self, text_data):
        """ Triggered when a poll is started or stopped. Should use the same logic
            as the http-request /live_question/.

            Additionally, on start/stop we need to render the
            live_poll_template.html template and broadcast it to the voters. The
            previous scheme was to just reload the page, but this is inefficient as
            it requires both an http and ws request.
        """
        # Data will contain "action" with either "start" or "stop" and "questionpk"
        # with an integer string 

        data = json.loads(text_data)
        print(data)

        import pdb; pdb.set_trace()
        if self.scope['user'].is_staff:
            question_pk = int(data['questionpk'])
            status   = data['action']

            try:
                question = PollQuestion.objects.get(pk = question_pk)
                course   = Course.objects.get(pk = self.course_pk)
            except Exception as e:
                raise e

            if status == 'endall': # State -1
                # Make sure this only kills the poll questsions for this course
                PollQuestion.objects.filter(
                        visible=True,
                        poll__course=question.poll.course
                        ).update(
                            visible=False, 
                            can_vote=False)
                response_data = {'response': 'Polling has ended'}

                # Send information to the voters
                state = str(question.pk)+"-"+str(question.can_vote)
                content = loader.render_to_string(
                        'polls/live_poll_template.html', 
                        {
                            'state': state,
                            'course': course,
                        }
                    )
                async_to_sync(self.channel_layer.group_send)(
                    self.voter_group_name,
                    {
                        'type': 'status_update',
                        'content': content,
                    }
                )
                #Group('Voter-'+course_pk).send({'text': json.dumps({'content': content})})

            # The PollQuestion model has built in functions for this. But we have to make sure
            # that this is the only live question on start.
            #
            # As of June 15, 2015, moved reset() to stop.
            elif status == 'start':
                # It is possible that the administrator accidentally hit the start button again.
                # We check to see if this is the case, and return an error message if so.
                if question.can_vote:
                    response_data = {'response': 'This question is already active'}
                else: 
                    # On 'start' we reset the poll. However, to avoid saving a bunch of empty polls
                    # we first check to see if any votes have been cast.
                    choices  = question.choices.filter(cur_poll=question.num_poll)
                    num_votes = sum(choices.values_list('num_votes', flat=True))
                    state = str(question.pk)+"-"+str(question.can_vote)

                    response_data = {'response': 'Question pushed to live page'}
                    if num_votes != 0:
                        pk_map = question.reset()
                        response_data['pkMap'] = pk_map
                    
                    # The model now takes care of this. Also, need to update for
                    # current course if reimplemented
                    # PollQuestion.objects.filter(visible=True).update(visible=False, can_vote=False)
                    question.start()

                    # Update the last-active 
                    course.update_last_active()

                    # Send information to the voters.
                    # Note that the choice_pk's may have reset wit hthe change in
                    # the poll number, so we must reload them
                    choices  = question.choices.filter(cur_poll=question.num_poll)
                    content = loader.render_to_string(
                            'polls/live_poll_template.html', 
                            {
                                'question': question, 
                                'choices': choices, 
                                'state': state, 
                                'votes': num_votes,
                                'course': course,
                            }
                        )

                    async_to_sync(self.channel_layer.group_send)(
                        self.voter_group_name,
                        {
                            'type': 'status_update',
                            'content': content,
                        }
                    )
                    #Group('Voter-'+course_pk).send({'text': json.dumps({'content': content})})
                    self.send_votes_to_admin(question, self.course_pk)
            elif status == 'stop':
                if not question.can_vote:
                    response_data = {'response': 'This question is not live.'}
                elif not question.visible:
                    response_data = {'response': 'That question is not visible'}
                else:
                    question.stop()
                    response_data = {'response': 'Question stopped. Displaying results.'}

                    choices  = question.choices.filter(cur_poll=question.num_poll)
                    num_votes = sum(choices.values_list('num_votes', flat=True))
                    state = str(question.pk)+"-"+str(question.can_vote)
                    content = loader.render_to_string(
                            'polls/live_poll_template.html', 
                            {
                                'question': question, 
                                'choices': choices, 
                                'state': state, 
                                'votes': num_votes,
                                'course': course,
                            }
                        )

                    async_to_sync(self.channel_layer.group_send)(
                        self.voter_group_name,
                        {
                            'type': 'status_update',
                            'content': content,
                        }
                    )
                    #Group('Voter-'+course_pk).send({'text': json.dumps({'content': content})})

            # Add the action to the response data, since it's used in figuring out
            # the page logic
            response_data['action'] = status
        else:
            response_data = {'response': 'You are not authorized to make this POST'}

#       Group("Admin-"+course_pk).send({'text': json.dumps(response_data)})
#       # Do this instead of self.send() in order to ensure that if same user is
#       # logged in on multiple devices, the devices all update
        async_to_sync(self.channel_layer.group_send)(
            self.admin_group_name,
            {
                'type': 'button_press',
                'content': response_data,
            }
        )
        #self.send(text_data=json.dumps(response_data))

    def button_press(self, event):

        content = event['content']
        self.send(text_data=json.dumps(content))

    def vote_update(self, event):

        content = event['content']
        self.send(text_data=json.dumps(content))

    def send_votes_to_admin(self, question, course_pk):
        """ Helper method that fires when someone votes. Used to update the number
            of votes seen on the poll admin page. Takes one argument 'question'
            which should be a Poll Question 
        """
        choices  = question.choices.filter(cur_poll=question.num_poll)
        num_votes = sum(choices.values_list('num_votes', flat=True))
        response_data= {'numVotes':  num_votes}
        for choice in choices:
            field = str(choice.pk)+"-votes"
            num_votes = str(choice.num_votes)
            response_data[field]=num_votes
        response_data['state'] = str(question.pk)+"-"+str(question.can_vote)

        async_to_sync(self.channel_layer.group_send)(
            self.admin_group_name,
            {
                'type': 'vote_update',
                'content': response_data,
            }
        )
        #Group('Admin-'+course_pk).send({'text': json.dumps(response_data)})



class PollVoteConsumer(WebsocketConsumer):

    def connect(self):
        """ Consumer for when a voter accesses the live poll for a certain course. 
            host/vote/{course_pk}/{poll_pk}. Group: Voter-{course_pk}
        """
        # Add to both the list of voters for the course, as well as establishing a
        # group for just this user
        user = self.scope["user"]
        self.course_pk = self.scope['url_route']['kwargs']['course_pk']
        self.voter_group_name = f"Voter-{self.course_pk}"
        self.admin_group_name = f"Admin-{self.course_pk}"

        async_to_sync(self.channel_layer.group_add)(
            self.voter_group_name,
            self.channel_name
        )

        #Group('Voter-'+course_pk).add(message.reply_channel)
        #Group('User-'+str(user.pk)).add(message.reply_channel)
        #message.reply_channel.send({'accept': True})

        self.accept()

    def disconnect(self, close_code):
        """ Disconnecting from live poll.  Remove from the group
        """
        user = self.scope["user"]
        
        async_to_sync(self.channel_layer.group_discard)(
            self.voter_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """ Triggered when a user votes. Should use the same logic
            as the http-request /query_live/ (POST).
        """
        # Message will have choicepk as field
        data = json.loads(text_data)
        print(data)

        if self.scope['user'].is_authenticated:
            choice_pk = int(data['choice_pk'])
            try:
                choice   = PollChoice.objects.get(pk=choice_pk)
            except Exception as e:
                print(str(e))

            # Get or create a StudentVote object
            # In particular, check to see if the student has voted in the current poll.
            # There is the potential here for race conditions, so we place the code
            # in an atomic manager, and use the select_for_update method to lock the
            # row
            with transaction.atomic():
                try:
                    svote, created = (StudentVote.objects.select_for_update()
                                        .get_or_create(
                                            student=self.scope['user'], 
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

    #        Group('Voter-'+course_pk).send({'text': json.dumps(response_data)})
    #        This is wrong. We need to send this to the individual user, not
    #        everyone in the course
    
            self.send(text_data=json.dumps(response_data))
            #Group('User-'+str(message.user.pk)).send({'text': json.dumps(response_data)})
            self.send_votes_to_admin(choice.question, self.course_pk)

    def status_update(self, event):
        #Group('Voter-'+course_pk).send({'text': json.dumps({'content': content})})
        content = event['content']
        self.send(text_data=json.dumps({'content': content}))

    def send_votes_to_admin(self, question, course_pk):
        """ Helper method that fires when someone votes. Used to update the number
            of votes seen on the poll admin page. Takes one argument 'question'
            which should be a Poll Question 
        """
        choices  = question.choices.filter(cur_poll=question.num_poll)
        num_votes = sum(choices.values_list('num_votes', flat=True))
        response_data= {'numVotes':  num_votes}
        for choice in choices:
            field = str(choice.pk)+"-votes"
            num_votes = str(choice.num_votes)
            response_data[field]=num_votes
        response_data['state'] = str(question.pk)+"-"+str(question.can_vote)

        async_to_sync(self.channel_layer.group_send)(
            self.admin_group_name,
            {
                'type': 'vote_update',
                'content': response_data,
            }
        )
        #Group('Admin-'+course_pk).send({'text': json.dumps(response_data)})

## Attached to websocket.connect
#@channel_session
#@channel_session_user_from_http
#def admin_connect(message, course_pk, poll_pk):
#    """ Consumer for when an administrator access the poll-admin feature. 
#        host/query_live/{course_pk}/{poll_pk}/poll_admin. Group: Admin-{course_pk}
#        Adds course_pk and poll_pk to session data.
#    """
#    message.channel_session['course_pk'] = course_pk
#    message.channel_session['poll_pk'] = poll_pk
#    
#    Group('Admin-'+course_pk).add(message.reply_channel)
#    message.reply_channel.send({'accept': True})
#
#@channel_session
#def admin_disconnect(message, course_pk, poll_pk):
#    """ Disconnecting from poll-admin.  Remove from the group
#    """
#    course_pk = message.channel_session['course_pk']
#    Group('Admin'+course_pk).discard(message.reply_channel)
#
## Attached to websocket.message
#@channel_session_user
#def admin_receive(message, course_pk, poll_pk):
#    """ Triggered when a poll is started or stopped. Should use the same logic
#        as the http-request /live_question/.
#
#        Additionally, on start/stop we need to render the
#        live_poll_template.html template and broadcast it to the voters. The
#        previous scheme was to just reload the page, but this is inefficient as
#        it requires both an http and ws request.
#    """
#    # Data will contain "action" with either "start" or "stop" and "questionpk"
#    # with an integer string 
#
#    data = json.loads(message['text'])
#
#    if message.user.is_staff:
#        question_pk = int(data['questionpk'])
#        status   = data['action']
#
#        try:
#            question = PollQuestion.objects.get(pk = question_pk)
#            course   = Course.objects.get(pk = course_pk)
#        except Exception as e:
#            print(str(e))
#
#        if status == 'endall': # State -1
#            # Make sure this only kills the poll questsions for this course
#            PollQuestion.objects.filter(
#                    visible=True,
#                    poll__course=question.poll.course
#                    ).update(
#                        visible=False, 
#                        can_vote=False)
#            response_data = {'response': 'Polling has ended'}
#
#            # Send information to the voters
#            state = str(question.pk)+"-"+str(question.can_vote)
#            content = loader.render_to_string(
#                    'polls/live_poll_template.html', 
#                    {
#                        'state': state,
#                        'course': course,
#                    }
#                )
#            Group('Voter-'+course_pk).send({'text': json.dumps({'content': content})})
#
#        # The PollQuestion model has built in functions for this. But we have to make sure
#        # that this is the only live question on start.
#        #
#        # As of June 15, 2015, moved reset() to stop.
#        elif status == 'start':
#            # It is possible that the administrator accidentally hit the start button again.
#            # We check to see if this is the case, and return an error message if so.
#            if question.can_vote:
#                response_data = {'response': 'This question is already active'}
#            else: 
#                # On 'start' we reset the poll. However, to avoid saving a bunch of empty polls
#                # we first check to see if any votes have been cast.
#                choices  = question.choices.filter(cur_poll=question.num_poll)
#                num_votes = sum(choices.values_list('num_votes', flat=True))
#                state = str(question.pk)+"-"+str(question.can_vote)
#
#                response_data = {'response': 'Question pushed to live page'}
#                if num_votes != 0:
#                    pk_map = question.reset()
#                    response_data['pkMap'] = pk_map
#                
#                # The model now takes care of this. Also, need to update for
#                # current course if reimplemented
#                # PollQuestion.objects.filter(visible=True).update(visible=False, can_vote=False)
#                question.start()
#
#                # Update the last-active 
#                course.update_last_active()
#
#                # Send information to the voters.
#                # Note that the choice_pk's may have reset wit hthe change in
#                # the poll number, so we must reload them
#                choices  = question.choices.filter(cur_poll=question.num_poll)
#                content = loader.render_to_string(
#                        'polls/live_poll_template.html', 
#                        {
#                            'question': question, 
#                            'choices': choices, 
#                            'state': state, 
#                            'votes': num_votes,
#                            'course': course,
#                        }
#                    )
#                Group('Voter-'+course_pk).send({'text': json.dumps({'content': content})})
#                send_votes_to_admin(question, course_pk)
#        elif status == 'stop':
#            if not question.can_vote:
#                response_data = {'response': 'This question is not live.'}
#            elif not question.visible:
#                response_data = {'response': 'That question is not visible'}
#            else:
#                question.stop()
#                response_data = {'response': 'Question stopped. Displaying results.'}
#
#                choices  = question.choices.filter(cur_poll=question.num_poll)
#                num_votes = sum(choices.values_list('num_votes', flat=True))
#                state = str(question.pk)+"-"+str(question.can_vote)
#                content = loader.render_to_string(
#                        'polls/live_poll_template.html', 
#                        {
#                            'question': question, 
#                            'choices': choices, 
#                            'state': state, 
#                            'votes': num_votes,
#                            'course': course,
#                        }
#                    )
#                Group('Voter-'+course_pk).send({'text': json.dumps({'content': content})})
#
#        # Add the action to the response data, since it's used in figuring out
#        # the page logic
#        response_data['action'] = status
#    else:
#        response_data = {'response': 'You are not authorized to make this POST'}
#
#    Group("Admin-"+course_pk).send({'text': json.dumps(response_data)})
#
#    # Need to add code to broadcast to voters that a change has occured
#
## Attached to websocket.connect
#@channel_session
#@channel_session_user_from_http
#def voter_connect(message, course_pk):
#    """ Consumer for when a voter accesses the live poll for a certain course. 
#        host/vote/{course_pk}/{poll_pk}. Group: Voter-{course_pk}
#    """
#    # Add to both the list of voters for the course, as well as establishing a
#    # group for just this user
#    user = message.user
#    Group('Voter-'+course_pk).add(message.reply_channel)
#    Group('User-'+str(user.pk)).add(message.reply_channel)
#    message.reply_channel.send({'accept': True})
#
#@channel_session
#def voter_disconnect(message, course_pk):
#    """ Disconnecting from live poll.  Remove from the group
#    """
#    user = message.user
#    Group('Voter-'+course_pk).discard(message.reply_channel)
#    Group('User-'+str(user.pk)).discard(message.reply_channel)
#
## Attached to websocket.message
#@channel_session_user
#def voter_receive(message, course_pk):
#    """ Triggered when a user votes. Should use the same logic
#        as the http-request /query_live/ (POST).
#    """
#    # Message will have choicepk as field
#    data = json.loads(message['text'])
#
#    if message.user.is_authenticated:
#        choice_pk = int(data['choice_pk'])
#        try:
#            choice   = PollChoice.objects.get(pk=choice_pk)
#        except Exception as e:
#            print(str(e))
#
#        # Get or create a StudentVote object
#        # In particular, check to see if the student has voted in the current poll.
#        # There is the potential here for race conditions, so we place the code
#        # in an atomic manager, and use the select_for_update method to lock the
#        # row
#        with transaction.atomic():
#            try:
#                svote, created = (StudentVote.objects.select_for_update()
#                                    .get_or_create(
#                                        student=message.user, 
#                                        cur_poll = choice.cur_poll, 
#                                        question=choice.question
#                                    )
#                                 )
#            except IntegrityError as dberror:
#                return HttpResponse('<h2>You have attempted to submit multiple votes</h2>')
#
#            if created: # First vote
#                svote.choice = choice;
#                svote.add_choice(choice)
#            else: # Revoting, so change the vote
#                if svote.vote != choice:
#                    svote.change_vote(choice)
#
#            response_data = {'status': 'success'}
#
##        Group('Voter-'+course_pk).send({'text': json.dumps(response_data)})
##        This is wrong. We need to send this to the individual user, not
##        everyone in the course
#        Group('User-'+str(message.user.pk)).send({'text': json.dumps(response_data)})
#        send_votes_to_admin(choice.question, course_pk)
#
#def send_votes_to_admin(question, course_pk):
#    """ Helper method that fires when someone votes. Used to update the number
#        of votes seen on the poll admin page. Takes one argument 'question'
#        which should be a Poll Question 
#    """
#    choices  = question.choices.filter(cur_poll=question.num_poll)
#    num_votes = sum(choices.values_list('num_votes', flat=True))
#    response_data= {'numVotes':  num_votes}
#    for choice in choices:
#        field = str(choice.pk)+"-votes"
#        num_votes = str(choice.num_votes)
#        response_data[field]=num_votes
#    response_data['state'] = str(question.pk)+"-"+str(question.can_vote)
#
#    Group('Admin-'+course_pk).send({'text': json.dumps(response_data)})
