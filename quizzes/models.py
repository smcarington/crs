from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

# Row based permissions
from guardian.models import UserObjectPermission

import re
import json
import random

class Course(models.Model):
    """ A container for storing multiple quizzes. Will only be visible to students
        who are enrolled in that course.
        name (Char) the name of the course
        open_enrollment (Boolean) whether any student can enroll
    """
    name = models.CharField(max_length=20)
    # Allows any student to enroll
    open_enrollment = models.BooleanField(default=False) 

    def add_admin(self, username):
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
            perm = 'can_edit_quiz'
            UserObjectPermission.objects.assign_perm(
                perm, user, obj=self
            )
        except Exception as e:
            print(e)

    @property
    def status(self):
        num_quizzes = self.quizzes.filter(
                live__lte=timezone.now(),
                expires__gt=timezone.now()).count()
        if num_quizzes:
            return "{} Active Quiz{}".format(
                num_quizzes, '' if num_quizzes==1 else 'zes')
        else:
            return "No Active Quiz"

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            ("can_edit_quiz", "Can edit the quiz"),
        )

class UserMembership(models.Model):
    """ Tracks which courses a student/ta can see. General use should be to get
    a UserMembership object according to user, then the um.courses.add(course)
    command.
    """
    user = models.OneToOneField(
        User, related_name='membership', on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        course_string = ''
        for course in self.courses.all():
            course_string += str(course)

        return "{}: {}".format(
            self.user.username,
            course_string)

class Quiz(models.Model):
    """ Container for holding a quiz. Quizzes consist of several MarkedQuestion
        objects. In particular, a Quiz object has the following attributes:
        name - (CharField) the name of the quiz
        tries - (IntegerField) The number of attempts a student is permitted to
            for the quiz. A value of tries=0 means unlimited attempts
        live  - (DateTimeField) The date on which the quiz becomes available to
            students
        expires - (DateTimeField) The date on which the quiz closes. 
        _cat_list - (TextField) Contains the category pool numbers. Has custom
            set/get methods to serialize the data.
        out_of - (IntegerField) The number of different MarkedQuestion pools. 
        immediate_solutions (Boolean) If true, students can see solutions at any
        time. If false, solutions are only available once the quiz has
        concluded.
    """
    course  = models.ForeignKey(
        Course, related_name='quizzes', on_delete=models.CASCADE)
    name    = models.CharField("Name", max_length=200)
    # Number of tries a student is allowed. A value of category=0 is equivalent to infinity.
    tries   = models.IntegerField("Tries", default=0)
    live    = models.DateTimeField("Live on")
    expires = models.DateTimeField("Expires on")
    immediate_solutions = models.BooleanField(default=True)
    _cat_list = models.TextField(null=True)
#    # Replaced as a property computed from _cat_list
#    out_of  = models.IntegerField("Points", default=1)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    @property
    def solutions_are_visible(self):
        """ Used to determine if students are currently allowed to see the
            solutions for this quiz.
        """
        return self.immediate_solutions or timezone.now() > self.expires


    # cat_list needs custom set/get methods to handle serialization
    @property
    def cat_list(self):
        return self._cat_list

    @cat_list.setter
    def cat_list(self, value):
        """ Sets the _cat_list attribute. value should be a list of integers
            indexing the category pools.
        """
        self._cat_list = json.dumps(value)
        self.save()

    @cat_list.getter
    def cat_list(self):
        return json.loads(self._cat_list)

    # The out_of field is now replaced by a property, equivalent to the number
    # of distinct category numbers
    @property
    def out_of(self):
        return len(self.cat_list)

    def update_out_of(self):
        """ Determines the number of MarkedQuestion pools in this quiz. Is
            called when MarkedQuestions are added/edited/deleted from the quiz.
        """
        cats = list(self.markedquestion_set.all().values_list('category', flat=True))
        # Make distinct
        cats = list(set(cats))
        self.cat_list = cats
        # Old technique,  before allowing for random question order
        # -- Important to base this on the max category, rather than number of questions
        # -- self.out_of = self.markedquestion_set.aggregate(Max('category'))['category__max']
        self.save()

    def get_random_question(self, index):
        """ Returns a random question from the category corresponding to
            cat_list[index]
            <<INPUT>>
            index (integer) - a non-negative integer no more than self.out_of.
                The quiz has an array enumerating the categories, and we pull a
                question from the category corresponding to index. For example,
                if cat_list = [1, 3, 4, 10] and index = 3, we choose a question
                from category=cat_list[index] = cat_list[3] = 10.
            <<OUTPUT>>
            (MarkedQuestion) The question.
        """
        # Get the category list and select the Marked Questions corresponding to
        # this category
        cat_list = self.cat_list
        marked_questions = self.markedquestion_set.filter(
                category=cat_list[index])
        return random.choice(marked_questions)

    def __str__(self):
        return self.name

class MarkedQuestion(models.Model):
    """ An instance of a question within a Quiz object. These are designed to
        have randomized inputs, and additionally can be assigned to a
        MarkedQuestion pool. For example, if three questions all belong to the
        same pool, then when a quiz is created, only one of these three
        questions will be chosen.
        quiz - (ForeignKey[Quiz]) The quiz to which the MarkedQuestion belongs
        category (IntegerField) The MarkedQuestion pool
        problem_str - (TextField) The question itself. Generated variables
            should be the form {v[0]}, {v[1]},..., etc. Should take LaTeX with
            delimiters \( \), though this looks horrific when escaped.
        num_vars - (IntegerField) Keeps track of the number of variables within
            the question
        choices - (TextField) The range that the variables are allowed to take
            on. Delimited by a colon.
        answer - (TextField) The correct answer. Should include {v[0]}, {v[i]}
            as well.
        functions - (TextField) User defined functions.
        q_type - (CharField) Can either be direct entry 'D' (student puts in a
            number) or multiple choice 'MC'. True/False is deprecated as it can
            be created with MC.
        mc_choices - (TextField) Used only when q_type = 'MC', and includes the
           multiple choice answers. These can include variables {v[i]} as well,
           and are delimited by a semi-colon.
    """
    quiz         = models.ForeignKey("Quiz", Quiz, null=True)
    # Keeps track of the global category, so that multiple questions can be used
    category     = models.IntegerField("Category", default=1)
    problem_str = models.TextField("Problem")
    choices      = models.TextField("Choices", null=True)
    num_vars     = models.IntegerField(null=True)
    answer       = models.TextField("Answer")
    functions    = models.TextField("Functions", default='{}')
    # Allows for multiple kinds of questions
    QUESTION_CHOICES = ( 
            ('D', 'Direct Entry'),
            ('MC', 'Multiple Choice'),
            ('TF', 'True/False'),
        )

    q_type      = models.CharField("Question Type",
                    max_length=2, 
                    choices=QUESTION_CHOICES,
                    default='D',
                  )
    mc_choices = models.TextField("Multiple Choice", default ='[]', blank=True)

    class Meta:
        ordering = ['quiz', 'category']
        verbose_name = "Marked Question"

    def save(self, *args, **kwargs):
        """ Override save so that set_num_vars is called automatically"""
        self.set_num_vars()
        super(MarkedQuestion, self).save(*args, **kwargs)

    # Whenever we set the problem_str, this function is called to update the
    # number of variables. It also validates that they are sequentially indexed
    def set_num_vars(self):
        """ Go through problem_str and check the variables {v[i]}. Ensure the
            'i' occur in sequential order, and throw an error otherwise
        """
        # Use a regex to find all instances of {v[i]}, but only capture the
        # variable indices. 
        list_of_vars = re.findall(r'{v\[(\d+)\]}', self.problem_str)
        # Find the distinct indices, convert them to integers, and sort
        list_of_vars = list(set(list_of_vars))
        list_of_vars = [int(var_ind) for var_ind in list_of_vars]
        list_of_vars = sorted(list_of_vars)
        # Now we check whether they are sequential
        if all(a==b for a,b in enumerate(list_of_vars, list_of_vars[0])):
            self.num_vars = len(list_of_vars)
        else:
            self.num_vars = None
            raise NonSequentialVariables(
                "Variables have non-sequential indices {}".format(list_of_vars)
            )

    def update(self, quiz):
        """ Updates the quiz to which this belongs, and updates that quiz's
            attributes as well. Called when adding/editing/deleting a
            MarkedQuestion.
        """
        self.quiz = quiz
        self.save()
        quiz.update_out_of()

    def get_random_choice(self):
        """ Returns a random choice"""
        return random.choice(self.choices.split(':'))

    def __str__(self):
        return self.problem_str

class StudentQuizResult(models.Model):
    """ When a student starts/writes a quiz, it creates a StudentQuizResult
        instance. This tracks which questions were generated in the quiz, which
        choices for the variables were made, how the student answered (both the
        direct input and how it was evaluated). 
        <<Attributes>>
        student - (ForeignKey[User]) The student who wrote the quiz
        quiz    - (ForeignKey[Quiz]) The quiz the student wrote
        attempt - (IntegerField) Which attempt does this StudentQuizResult
            correspond to.
        cur_quest - (IntegerField) This object is updated each time the student
            completes a question. This tracks which question the student is on,
            allowing the student to leave during a quiz and resume again later.
        result - (TextField) String serialized as a JSON object. 
        score - (IntegerField) The score the student achieved in this question.
        _q_order - (Private: JSON serialized list) A randomization of the array
            [0,1,2,...,quiz.out_of-1] indicating the order of indices to pull 
            from quiz.cat_list. Allows for non-sequential ordering of
            categories. For example, if 
                quiz.cat_list = [1, 3, 4, 10*]
                quiz.out_of   = 4
                _q_order      = [1, 0, 3, 2*]
            then question cur_quest = 4 corresponds to
            pool = cat_list[_q_order[cur_quest-1]] = cat_list[_q_order[3]] 
                 = cat_list[2] = 10.
    """
    student   = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz      = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    attempt   = models.IntegerField(null=True, default=1) #track which attempt this is
    #track which question the student is on if they leave. If cur_question = 0 then completed
    cur_quest = models.IntegerField(null=True, default=1) 

    # The result is a json string which serializes the question data. For example
    # result = {
    #           '1': {
    #                   'pk': '13',
    #                   'inputs': '1;2;3', 
    #                   'score': '0',
    #                   'answer': 22.3,
    #                   'guess_string': '-22.3*cos(pi)',
    #                   'guess': 15.7,
    #                   'type': 'D',
    #                 },
    #           '2': {
    #                   'pk: '52'
    #                   'inputs': '8;-2', 
    #                   'score': '1',
    #                   'answer': 3.226,
    #                   'guess': '3.226',
    #                   'guess_string': '3.226',
    #                   'type': 'MC',
    #                   'mc_choices': ['3.226', '14', '23', '5.22'],
    #                 },
    #          }
    #          Indicates that the first question is a MarkedQuestion with pk=13, the inputs to
    #          this question were v=[1,2,3], and the student got the question wrong with a guess of 15.7
    result  = models.TextField(default='{}')
    score   = models.IntegerField(null=True)
    _q_order = models.TextField(default='')

    class Meta:
        verbose_name = "Quiz Result"

    @property
    def q_order(self):
        return json.loads(self._q_order)

    @q_order.setter
    def q_order(self, value):
        """ Value should be a list of integers """
        self._q_order = json.dumps(value)
        self.save()

    def update_score(self, minus=False):
        """ Adds one to the overall score """
        if minus:
            self.score -= 1
        else:
            self.score += 1
        self.save()

    def update_result(self, result):
        """ Takes a python dictionary, serializes it, and stores it in the result column.
            Input: result (dict) - the python dictionary.
            Output: Void
        """
        self.result = json.dumps(result)
        self.save()

    def get_result(self):
        """ Returns a python dictionary with the student quiz results
            Input: None
            Output: result (dict) - The python dictionay of results
                    attempt (string) - The current attempt, as a string to access in result
        """
        result = json.loads(self.result)
        attempt = str(self.cur_quest)
        return result, attempt

    def add_question_number(self):
        """ Adds one to the cur_quest field. However, checks if we have surpassed the last question,
            and if so sets cur_quest to 0.
            Input: None
            Output: is_last (Boolean) - indicated whether the cur_quest field has been set to 0
            TODO: Change this to allow for non-sequential numbering of
                  categories
        """
        num_quests = self.quiz.out_of
        if self.cur_quest == num_quests:
            is_last = True
            self.cur_quest = 0
        else:
            is_last = False
            self.cur_quest += 1
        self.save()
        
        return is_last

    @classmethod
    def create_new_record(cls, student, quiz, attempt=1):
        """ Creates a new StudentQuizResult record, instantiating a lot of
            redundant information.
            <<INPUT>>
            student (User) 
            quiz (Quiz)
            attempt (Integer default 1) The attempt number
        """
        # Create _q_order by randomizing the sequence [0,1,2,...,quiz.out_of-1]
        order = [x for x in range(0,quiz.out_of)]
        random.shuffle(order)
        order = json.dumps(order)
        new_record = cls(
            student=student, quiz=quiz, attempt=attempt,
            score=0, result='{}', cur_quest=1,
            _q_order = order
        )
        new_record.save()
        return new_record

 
    def __str__(self):
        return self.student.username + " - " + self.quiz.name + " - Attempt: " + str(self.attempt)


class CSVFile(models.Model):
    """ Used for storing CSV files.
    """
    doc_file  = models.FileField(upload_to="tmp/")

    def __str__(self):
        return self.doc_file


# --------- Marks (fold) ------- #


class Evaluation(models.Model):
    """ Model used to track events to which students receive grades. 
    """
    name = models.CharField(max_length=200)
    out_of = models.IntegerField(default=0)
    course = models.ForeignKey(Course, null=True,
            on_delete=models.CASCADE)

    def quiz_update_out_of(self, quiz):
        """ If the exemption corresponds to a quiz, we update the out_of category
        """
        self.out_of = quiz.out_of
        self.save()

    def __str__(self):
        return self.name

class StudentMark(models.Model):
    """ Tracks a student's mark. 
        <<INPUT>>
        user (User) the student
        evaluation (Evaluation) The evaluation object (quiz, test, etc)
        score (Float) The score (relative to evaluation.out_of)
    """
    user = models.ForeignKey(User, related_name='marks', 
            on_delete=models.CASCADE)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)
    score = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['user__username', 'evaluation']

    def set_score(self, score, method=''):
        """ Method to set the score. Allows input of method which determines how to set the score.
            Input: score (float) - the value to update
                   method (String) - 'HIGH' only update the score if the input score is higher
              Out: old_score (float)  - the old score, for logging purposes
        """

        old_score = self.score

        if method == 'HIGH':
            self.score = max(self.score or 0, score)
        else:
            self.score = score

        self.save()

        return old_score

    def __str__(self):
        return "{user}: {score} in {category}".format(user=self.user, category=self.evaluation.name, score=str(self.score)) 

# --------- Marks (end) ------- #

#Exception for MarkedQuestion validation of num_vars
class NonSequentialVariables(Exception):
    pass



