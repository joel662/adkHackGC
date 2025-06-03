import unittest
import pandas as pd
import re
import os
from unittest.mock import patch

class TestCourseMerger(unittest.TestCase):

    def setUp(self):
        # Create dummy data for testing
        self.audit_sheet_file = "Audit Sheet.xlsx"
        self.past_courses_file = "past_courses.xlsx"
        self.output_file = "plannedCourse.csv"

        self.audit_sheet_data = pd.DataFrame({
            0: ["COSC3106 (3CR)", "COSC3127 (3CR)", "COSC1046 (3CR)", "MATH1000 (3CR)"],
            1: ["25SP", "CR", "21F", "22FA"],
            2: [None, None, None, None]
        })
        self.audit_sheet_data.to_excel(self.audit_sheet_file, index=False, header=False)

        self.past_courses_data = pd.DataFrame({
            "Term": ["21F"],
            "Course Code": ["COSC1046"],
            "Course Name": ["Introduction to Computer Science I"],
            "Grade": [91],
            "Credit": [3]
        })
        self.past_courses_data.to_excel(self.past_courses_file, index=False)


    def tearDown(self):
        # Clean up created files after each test
        for file in [self.audit_sheet_file, self.past_courses_file, self.output_file]:
            if os.path.exists(file):
                os.remove(file)

    @patch('pandas.read_excel')
    @patch('pandas.DataFrame.to_csv')
    def test_process_audit_sheet_normal_case(self, mock_to_csv, mock_read_excel):
        # Mock the excel reading function
        mock_read_excel.return_value = self.audit_sheet_data

        # Run the code
        import importlib
        importlib.reload(sys.modules[__name__]) # Reload the module to run the code

        # Assert that to_csv was called with the correct filename.
        mock_to_csv.assert_called_once()
        self.assertTrue(self.output_file in mock_to_csv.call_args.args)

        # Read the output file and check the results.
        expected_output_data = pd.DataFrame({
            "Term": ["25SP", "21F", "22FA"],
            "Course Code": ["COSC3106", "COSC1046", "MATH1000"],
            "Status": ["To be Registered", "To be Registered", "To be Registered"],
            "Credits": [0, 0, 0],
            "Notes": ["Predicted Term: 25SP", "Predicted Term: 21F", "Predicted Term: 22FA"]
        })

        output_df = pd.read_csv(self.output_file)
        pd.testing.assert_frame_equal(output_df.reset_index(drop=True), expected_output_data.reset_index(drop=True))


    @patch('pandas.read_excel')
    @patch('pandas.DataFrame.to_csv')
    def test_process_audit_sheet_with_completed_course(self, mock_to_csv, mock_read_excel):
        # Mock the excel reading function
        audit_data = pd.DataFrame({
            0: ["COSC3106 (3CR)", "COSC3127 (3CR)"],
            1: ["25SP", "CR"],
        })
        mock_read_excel.return_value = audit_data

        import importlib
        importlib.reload(sys.modules[__name__])

        # Assert that to_csv was called with the correct filename.
        mock_to_csv.assert_called_once()
        self.assertTrue(self.output_file in mock_to_csv.call_args.args)
        # Read the output file and check the results.
        expected_output_data = pd.DataFrame({
            "Term": ["25SP"],
            "Course Code": ["COSC3106"],
            "Status": ["To be Registered"],
            "Credits": [0],
            "Notes": ["Predicted Term: 25SP"]
        })
        output_df = pd.read_csv(self.output_file)
        pd.testing.assert_frame_equal(output_df.reset_index(drop=True), expected_output_data.reset_index(drop=True))


    @patch('pandas.read_excel')
    @patch('pandas.DataFrame.to_csv')
    def test_process_audit_sheet_with_no_term(self, mock_to_csv, mock_read_excel):
        # Mock the excel reading function.  No term is provided.
        audit_data = pd.DataFrame({
            0: ["COSC3106 (3CR)"],
            1: [None],
        })
        mock_read_excel.return_value = audit_data
        import importlib
        importlib.reload(sys.modules[__name__])

        mock_to_csv.assert_called_once()
        self.assertTrue(self.output_file in mock_to_csv.call_args.args)

        # Read the output file and check the results.
        expected_output_data = pd.DataFrame({
            "Term": [None],
            "Course Code": ["COSC3106"],
            "Status": ["To be Registered"],
            "Credits": [0],
            "Notes": [""]
        })
        output_df = pd.read_csv(self.output_file)
        pd.testing.assert_frame_equal(output_df.reset_index(drop=True), expected_output_data.reset_index(drop=True))

    @patch('pandas.read_excel')
    @patch('pandas.DataFrame.to_csv')
    def test_process_audit_sheet_with_empty_audit_sheet(self, mock_to_csv, mock_read_excel):
        # Mock the excel reading function.  Empty audit sheet.
        audit_data = pd.DataFrame({0: [], 1: []})
        mock_read_excel.return_value = audit_data
        import importlib
        importlib.reload(sys.modules[__name__])
        mock_to_csv.assert_called_once()
        self.assertTrue(self.output_file in mock_to_csv.call_args.args)

        # Read the output file and check the results.
        expected_output_data = pd.DataFrame({
            "Term": [],
            "Course Code": [],
            "Status": [],
            "Credits": [],
            "Notes": []
        })
        output_df = pd.read_csv(self.output_file)
        pd.testing.assert_frame_equal(output_df.reset_index(drop=True), expected_output_data.reset_index(drop=True))

    @patch('pandas.read_excel')
    @patch('pandas.DataFrame.to_csv')
    def test_specific_cells_processing_normal(self, mock_to_csv, mock_read_excel):
      # Mock the excel reading function
        audit_data = pd.DataFrame({
            'A': ['COSC3106 (3CR)'],
            'B': ['25SP'],
            'E': ['COSC1046'],
            'F': ['21F'],
            'G': ['MATH1000'],
            'H': ['22FA']
        })
        mock_read_excel.return_value = audit_data
        import importlib
        importlib.reload(sys.modules[__name__])

        mock_to_csv.assert_called_once()
        self.assertTrue(self.output_file in mock_to_csv.call_args.args)

        # Read the output file and check the results.
        expected_output_data = pd.DataFrame({
            "Term": ['25SP', '21F', '22FA'],
            "Course Code": ['COSC3106', 'COSC1046', 'MATH1000'],
            "Status": ['To be Registered', 'To be Registered', 'To be Registered'],
            "Credits": [0, 3, 3],
            "Notes": ['Predicted Term: 25SP', 'Predicted Term: 21F', 'Predicted Term: 22FA']
        })

        output_df = pd.read_csv(self.output_file)
        pd.testing.assert_frame_equal(output_df.reset_index(drop=True), expected_output_data.reset_index(drop=True))

    @patch('pandas.read_excel')
    @patch('pandas.DataFrame.to_csv')
    def test_specific_cells_processing_no_term(self, mock_to_csv, mock_read_excel):
      # Mock the excel reading function
        audit_data = pd.DataFrame({
            'E': ['COSC1046'],
            'F': [None],
            'G': ['MATH1000'],
            'H': [None]
        })
        mock_read_excel.return_value = audit_data
        import importlib
        importlib.reload(sys.modules[__name__])

        mock_to_csv.assert_called_once()
        self.assertTrue(self.output_file in mock_to_csv.call_args.args)

        # Read the output file and check the results.
        expected_output_data = pd.DataFrame({
            "Term": [None, None],
            "Course Code": ['COSC1046', 'MATH1000'],
            "Status": ['To be Registered', 'To be Registered'],
            "Credits": [3, 3],
            "Notes": ['', '']
        })

        output_df = pd.read_csv(self.output_file)
        pd.testing.assert_frame_equal(output_df.reset_index(drop=True), expected_output_data.reset_index(drop=True))

    @patch('pandas.read_excel')
    @patch('pandas.DataFrame.to_csv')
    def test_specific_cells_processing_completed(self, mock_to_csv, mock_read_excel):
      # Mock the excel reading function
        audit_data = pd.DataFrame({
            'E': ['COSC1046'],
            'F': ['CR'],
            'G': ['MATH1000'],
            'H': ['CR']
        })
        mock_read_excel.return_value = audit_data
        import importlib
        importlib.reload(sys.modules[__name__])

        mock_to_csv.assert_called_once()
        self.assertTrue(self.output_file in mock_to_csv.call_args.args)

        # Read the output file and check the results.
        expected_output_data = pd.DataFrame({
            "Term": [None, None],
            "Course Code": ['COSC1046', 'MATH1000'],
            "Status": ['Completed', 'Completed'],
            "Credits": [3, 3],
            "Notes": ['', '']
        })

        output_df = pd.read_csv(self.output_file)
        pd.testing.assert_frame_equal(output_df.reset_index(drop=True), expected_output_data.reset_index(drop=True))

import sys
if __name__ == '__main__':
    unittest.main()