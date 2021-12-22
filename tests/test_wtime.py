from unittest import TestCase

from wtime.wtime import Timer, tick


class TestTimer(TestCase):
    def test_tick(self) -> None:
        timer = Timer(time_left=10, topic="Unchanged")
        tick(timer)
        self.assertTrue(timer.time_left, 9)
        self.assertEqual(timer.topic, "Unchanged")
        with self.assertRaises(AttributeError):
            tick(Timer(time_left=0, topic="Bar"))
