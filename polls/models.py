from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

from guardian.models import UserObjectPermission

class Course(models.Model):
    """ A container for storing multiple polls. Will only be visible to students
        who are enrolled in that course.
    """
    name = models.CharField(max_length=20)
    open_enrollment = models.BooleanField(default=False)
    last_active = models.DateTimeField(blank=True, null=True)

    def update_last_active(self):
        self.last_active = timezone.now()
        self.save()

    def add_admin(self, username, staff=False):
        """ Adds row level adminstrative abilities for the specified user. Takes
        an optional parameter 'staff' (default False) which indicates whether
        the user is staff or admin. Admin have the permission 'can_edit_poll'
        while staff have 'can_see_poll_admin'.
        """
        try:
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = True
            user.save()

            # Make sure the user is also a part of the course
            membership, _ = UserMembership.objects.get_or_create(user=user)
            membership.courses.add(self)

            # Give the user permission to edit this course
            perm = 'can_see_poll_admin' if staff else 'can_edit_poll'
            UserObjectPermission.objects.assign_perm(
                perm, user, obj=self
            )
        except Exception as e:
            print(e)

    def get_num_polls(self):
        return self.poll_set.count()

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ("can_see_poll_admin", "Can see the poll administration"),
            ("can_edit_poll", "Can edit the poll"),
        )

class UserMembership(models.Model):
    """ Tracks which courses a student/ta can see
    """
    user = models.ForeignKey(User)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        course_string = ''
        for course in self.courses.all():
            course_string += str(course)

        return "{}: {}".format(
            self.user.username,
            course_string)

class Poll(models.Model):
    """ A container for multiple PollQuestion objects. Is linked to a particular
    course.  
    """
    title  = models.CharField(max_length=200)
    course = models.ForeignKey(Course)

    def __str__(self):
        return "{}: {}".format(self.course.name, self.title)

class PollQuestion(models.Model):
    """ A questions within a poll. 
    """
    poll     = models.ForeignKey(Poll, related_name="questions")
    text     = models.TextField(blank=True) # The question itself
    live     = models.BooleanField(default=False) # Question is being voted on
    num_poll = models.IntegerField(default=1) # Poll might be asked multiple times
    visible  = models.BooleanField(default=False) # Can students see this after the poll is finished
    can_vote = models.BooleanField(default=False)
    position = models.IntegerField(default=0) # Position amongst the other polls

    # Called when an administrator pushes the poll to the live page. View handles
    # setting all other visibility settings to false. To do: Those view commands
    # should be made a model method
    def start(self):
        # If this is already live, do nothing
        if self.visible and self.can_vote:
            return

        # Turn off all other questions for the same course
        self.poll.questions.filter(
                visible=True,
                poll__course=self.poll.course,
                ).update(
                    visible=False, 
                    can_vote=False
                    )

        # Set this to live
        self.visible  = True
        self.can_vote = True
        self.save()

    def stop(self):
        self.can_vote = False
        self.save()

    def reset(self):
        # Clone the choices, update cur_poll and num_poll. Returns a dictionary
        # item containing the map of primary keys
        clones = self.choices.filter(cur_poll=self.num_poll).order_by('id')
        self.num_poll = self.num_poll+1
        self.save()

        # By setting the clone pk=None, the save method creates a new instance of the model.
        # We must still manually reset the number of votes though. In addition, for the change
        # in the poll-admin page, we need to return a map of how the primary keys have changed.
        pk_map = {}
        for clone in clones:
            old_pk = str(clone.pk)

            # Reset the clone
            clone.cur_poll = self.num_poll
            clone.pk = None
            clone.num_votes = 0
            clone.save()

            # Get the new pk and add it to the pk_map
            new_pk = str(clone.pk)
            pk_map[old_pk]=new_pk

        return pk_map

    def move_position(self, direction):
        """ Change the position of a PollQuestion item. Handles the problem of 
            changing neighbouring position numbers as well. 
            Input : direction - A (String) indicating either 'up' or 'down'.
            Output: status - An integer indicating the success state.
                             -2 ~ no neighbouring object
                              1 - success
        """
        # Grab the neighbour. Throw an appropriate error.
        cur_pos = self.position
        try:
            if direction == "up":
                # neighbour = PollQuestion.objects.get(poll=self.poll,position=cur_pos-1)
                # To more easily deal with deletions, instead of reseting the positions on 
                # deletion, just get the nearest neighbour. Do this by getting all questions
                # with higher position, and ordering them so that the closest is in the first position.

                neighbours = PollQuestion.objects.filter(
                                poll=self.poll, 
                                position__lt=cur_pos).order_by('-position')
                if len(neighbours)==0:
                    return -2
            elif direction == "down":
                neighbours = PollQuestion.objects.filter(
                                poll=self.poll, 
                                position__gt=cur_pos).order_by('position')
                if len(neighbours)==0:
                    return -2
        except PollQuestion.DoesNotExist:
                return -2

        neighbour = neighbours[0]
        
        self.position = neighbour.position
        neighbour.position = cur_pos

        self.save()
        neighbour.save()

        return 1

    def __str__(self):
        try:
            return "Poll {number}: {text}".format(number=self.poll.pk, text=self.text[0:20])
        except Exception as e:
            return str(e)


class PollChoice(models.Model):
    """ Each poll has multiple choice answers. These also track how many votes
        each answer has received. When a poll is reset, these must be cloned.
    """
    question  = models.ForeignKey(PollQuestion, related_name="choices")
    text      = models.CharField(max_length=400)
    num_votes = models.IntegerField(default=0)
    cur_poll  = models.IntegerField(default=1)

    class Meta:
        ordering = ['pk']

    def add_vote(self):
        self.num_votes = self.num_votes+1
        self.save()

    def sub_vote(self):
        if self.num_votes == 0:
            raise Exception('Already zero votes')
        else:
            self.num_votes = self.num_votes-1
            self.save()

    def __str__(self):
        return "Poll: {} Question: {}, Choice: {}".format(
                self.question.poll.title,
                self.question.text[0:30], 
                self.text)

class StudentVote(models.Model):
    """ Tracks an individual student's vote. 
    """
    student  = models.ForeignKey(User)
    question = models.ForeignKey(PollQuestion, null=True)
    vote     = models.ForeignKey(PollChoice, related_name="votes", null=True)
    cur_poll = models.IntegerField(default=1)

    #class Meta:
    #    unique_together = ('student', 'question', 'cur_poll')

    def add_choice(self, choice):
        """ In a new vote, and the choice, save it, and increment the PollChoice object
            Input: vote (PollChoice) - The choice to add to the StudentVote element
            Return: void
        """
        self.vote = choice;
        self.save()
        choice.add_vote()

    def change_vote(self, new_vote):
        """ Changes the vote.
            Input: new_vote (PollChoice) - The new vote
            Return: void
        """

        old_vote = self.vote
        old_vote.sub_vote() 
        # Now that we've remove the last vote, we change the vote element and update it's count
        self.vote = new_vote
        self.save()
        new_vote.add_vote()

    def __str__(self):
        return self.student.username + ' vote '


class CSVFile(models.Model):
    """ Used for storing CSV files.
    """
    doc_file  = models.FileField(upload_to="tmp/")

    def __str__(self):
        return self.doc_file
