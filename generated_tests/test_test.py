import unittest
from unittest.mock import patch, MagicMock
import os
from test import main, PROJECT_ID, LOCATION  # Directly import from the file

class TestMain(unittest.TestCase):
    @patch('test.vertexai.init')
    @patch('test.GenerativeModel')
    @patch('builtins.input', side_effect=["hello", "exit"])
    @patch('builtins.print')
    def test_main_interaction_success(self, mock_print, mock_input, mock_generative_model, mock_vertexai_init):
        # Mock the GenerativeModel and its generate_content method
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "Hello, world!"
        mock_generative_model.return_value = mock_model_instance

        # Run the main function
        main()

        # Assertions
        mock_vertexai_init.assert_called_once_with(project=PROJECT_ID, location=LOCATION)
        mock_generative_model.assert_called_once_with("gemini-2.0-flash-lite-001")
        self.assertEqual(mock_input.call_count, 2) # Check if input was called twice
        self.assertEqual(mock_print.call_count, 3) # Check print was called as expected
        mock_print.assert_any_call("Gemini:", "Hello, world!")

    @patch('test.vertexai.init')
    @patch('test.GenerativeModel')
    @patch('builtins.input', side_effect=["hello", "exit"])
    @patch('builtins.print')
    def test_main_interaction_exception(self, mock_print, mock_input, mock_generative_model, mock_vertexai_init):
        # Mock the GenerativeModel and its generate_content method to raise an exception
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = Exception("Simulated error")
        mock_generative_model.return_value = mock_model_instance

        # Run the main function
        main()

        # Assertions
        mock_vertexai_init.assert_called_once_with(project=PROJECT_ID, location=LOCATION)
        mock_generative_model.assert_called_once_with("gemini-2.0-flash-lite-001")
        self.assertEqual(mock_input.call_count, 2)
        self.assertEqual(mock_print.call_count, 3)
        mock_print.assert_any_call("❌ Error:", "Simulated error")

    @patch('test.vertexai.init')
    @patch('test.GenerativeModel')
    @patch('builtins.input', side_effect=["exit"])
    @patch('builtins.print')
    def test_main_exit(self, mock_print, mock_input, mock_generative_model, mock_vertexai_init):

        # Run the main function
        main()

        # Assertions
        mock_vertexai_init.assert_called_once_with(project=PROJECT_ID, location=LOCATION)
        mock_generative_model.assert_called_once_with("gemini-2.0-flash-lite-001")
        self.assertEqual(mock_input.call_count, 1)
        self.assertEqual(mock_print.call_count, 1)
        mock_print.assert_called_once_with("🤖 Gemini Agent is ready. Type 'exit' to quit.")