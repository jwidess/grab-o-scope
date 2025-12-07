import unittest
from src.core.grabber_wrapper import GrabberWrapper

class TestGrabberWrapper(unittest.TestCase):

    def setUp(self):
        self.wrapper = GrabberWrapper()

    def test_initialization(self):
        self.assertIsNotNone(self.wrapper)

    def test_run_grab_o_scope(self):
        # Assuming run_grab_o_scope is a method in GrabberWrapper that executes the script
        result = self.wrapper.run_grab_o_scope("test_base_name")
        self.assertTrue(result)  # Adjust based on expected outcome

    def test_handle_output(self):
        # Assuming handle_output is a method that processes the output from the script
        output = self.wrapper.handle_output("test_output.png")
        self.assertIsNotNone(output)  # Adjust based on expected outcome

if __name__ == '__main__':
    unittest.main()