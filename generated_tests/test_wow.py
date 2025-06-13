import unittest
from io import StringIO
import sys
from wow import print

class TestWow(unittest.TestCase):
    def test_print_statement(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        print("pushes failed code final")
        sys.stdout = sys.__stdout__
        self.assertEqual(captured_output.getvalue().strip(), "pushes failed code final")

if __name__ == '__main__':
    unittest.main()