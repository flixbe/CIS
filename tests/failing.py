import unittest

class TestFailing(unittest.TestCase):
    def failing(self):
        self.fail("Failing")