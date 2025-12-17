import os
from unittest import TestCase


class BaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        # Change the working directory to the script's directory
        cls.original_working_directory = os.getcwd()
        tests_dir  = os.path.dirname(os.path.abspath(__file__))
        os.chdir(tests_dir)

    @classmethod
    def tearDownClass(cls):
        # Restore the original working directory
        os.chdir(cls.original_working_directory)
