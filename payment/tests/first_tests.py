from django.test import TestCase


class UtilityTestCase(TestCase):
    # Test cases for generate_random_id

    def setUp(self) -> None:
        self.number = 1

    def dumb_test(self):
        self.assertNotEqual(self.number, 2)
