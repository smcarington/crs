from django.test import TestCase
from .models import *

# Create your tests here.

class PollsTest(TestCase):
    """ Checks the Courses and Polls model.
    """

    fixtures = ['PollFixture']

    def test_poll_start_stop_reset(self):
        poll = Poll.objects.get(title="May 16/17")
        pq_one = poll.questions.get(text__startswith="You have a")
        pq_two = poll.questions.get(text__startswith="Which")
        pq_three = PollQuestion.objects.get(pk=267) # From a different class


        # Make this question live
        pq_one.start()
        self.assertTrue(pq_one.visible)
        self.assertTrue(pq_one.can_vote)
        self.assertFalse(pq_three.visible)
        self.assertFalse(pq_three.can_vote)

        # Get another question and make it live. pq_one should shut down
        pq_two.start()
        pq_one.refresh_from_db()
        self.assertTrue(not pq_one.visible)
        self.assertTrue(not pq_one.can_vote)
        self.assertTrue(pq_two.visible)
        self.assertTrue(pq_two.can_vote)

        # Running start on pq_two again should not change anything
        pq_two.start()
        pq_one.refresh_from_db()
        pq_two.refresh_from_db()
        self.assertTrue(not pq_one.visible)
        self.assertTrue(not pq_one.can_vote)
        self.assertTrue(pq_two.visible)
        self.assertTrue(pq_two.can_vote)

        # Stop pq_two
        pq_two.stop()
        pq_two.refresh_from_db()

        self.assertTrue(pq_two.visible)
        self.assertFalse(pq_two.can_vote)

        # Start both pq_two and pq_three. Since they are from different courses,
        # they should not affect each other
        pq_two.start(); pq_three.start();
        pq_two.refresh_from_db(); pq_three.refresh_from_db()
        self.assertTrue(pq_two.visible)
        self.assertTrue(pq_two.can_vote)
        self.assertTrue(pq_three.visible)
        self.assertTrue(pq_three.can_vote)

        # Stopping one should have no affect on the other
        pq_three.stop(); pq_three.refresh_from_db(); pq_two.refresh_from_db();
        self.assertTrue(pq_two.visible)
        self.assertTrue(pq_two.can_vote)
        self.assertTrue(pq_three.visible)
        self.assertFalse(pq_three.can_vote)

    def test_position_swap(self):
        pq_one = PollQuestion.objects.get(poll__pk=6, position=3)
        pq_two = PollQuestion.objects.get(poll__pk=6, position=4)

        # These fixtures are chosen because they are neighbours
        self.assertEqual(pq_one.position, 3)
        self.assertEqual(pq_two.position, 4)

        pq_two.move_position('up')
        pq_two.refresh_from_db(); pq_one.refresh_from_db()
        self.assertEqual(pq_one.position, 4)
        self.assertEqual(pq_two.position, 3)

        pq_two.move_position('down')
        pq_two.refresh_from_db(); pq_one.refresh_from_db()
        self.assertEqual(pq_one.position, 3)
        self.assertEqual(pq_two.position, 4)
