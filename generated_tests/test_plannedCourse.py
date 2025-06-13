import unittest
import pandas as pd
import os
from plannedCourse import audit_sheet_file, output_file, course_data, audit_cleaned_df
from plannedCourse import re
from unittest.mock import patch

class TestPlannedCourse(unittest.TestCase):

    def setUp(self):
        # Create dummy Audit Sheet.xlsx for testing
        self.audit_sheet_data = {
            0: ["COSC1000 (3CR)", "23FA"],
            1: ["COSC1001 (3CR)", "CR"],
            2: ["COSC2000 (3CR)", "24SP"],
            3: ["COSC3106 (3CR)", "CR"],
            4: ["COSC3127 (3CR)", "25SP"],
            5: ["COSC4000 (3CR)", "CR"],
            6: ["COSC4900 (3CR)", "24FA"],
            7: ["MATH1000 (3CR)", "CR"]
        }
        self.audit_sheet_df = pd.DataFrame(self.audit_sheet_data)
        self.audit_sheet_df.to_excel(audit_sheet_file, index=False, header=False)

        self.expected_output = pd.DataFrame({
            "Term": ["23FA", "24SP", "25SP", "24FA"],
            "Course Code": ["COSC1000", "COSC2000", "COSC3127", "COSC4900"],
            "Status": ["To be Registered", "To be Registered", "To be Registered", "To be Registered"],
            "Credits": [0, 0, 0, 0],
            "Notes": ["Predicted Term: 23FA", "Predicted Term: 24SP", "Predicted Term: 25SP", "Predicted Term: 24FA"]
        })

    def tearDown(self):
        # Clean up created files
        if os.path.exists(audit_sheet_file):
            os.remove(audit_sheet_file)
        if os.path.exists(output_file):
            os.remove(output_file)

    def test_audit_sheet_file_exists(self):
        self.assertTrue(os.path.exists(audit_sheet_file))

    def test_extract_course_data(self):
        # Check if the course data extraction is correct.
        # The implementation is correct only for the sample input
        # It should have a good check for the terms
        # It will have to check only the courses that are not marked as "CR"
        # And terms that follow the format such as 23FA, 24SP etc.
        # We can create an assertion for the length of the course data extracted

        # Create an expected_course_data based on test data
        expected_course_data = [
            ['23FA', 'COSC1000', 'To be Registered', 0, 'Predicted Term: 23FA'],
            ['24SP', 'COSC2000', 'To be Registered', 0, 'Predicted Term: 24SP'],
            ['25SP', 'COSC3127', 'To be Registered', 0, 'Predicted Term: 25SP'],
            ['24FA', 'COSC4900', 'To be Registered', 0, 'Predicted Term: 24FA']
        ]
        # Check if the length of course_data is correct
        # Check the extracted course data against the expected course data
        self.assertEqual(len(course_data), len(expected_course_data))

        # Test if the audit_cleaned_df is created properly
        # Convert the extracted data into DataFrame for comparison

        audit_cleaned_df_test = pd.DataFrame(course_data, columns=["Term", "Course Code", "Status", "Credits", "Notes"])

        pd.testing.assert_frame_equal(audit_cleaned_df_test.sort_values(by=['Course Code']).reset_index(drop=True), self.expected_output.sort_values(by=['Course Code']).reset_index(drop=True))


    def test_output_file_created(self):
         #Run the main part of the code before testing
        output_file = "plannedCourse.csv"
        # The output file will be created in the same directory
        self.assertTrue(os.path.exists(output_file))

    def test_output_file_content(self):
        # Read the output file and check its content against the expected output
        output_df = pd.read_csv(output_file)
        # Ensure the dataframes are equal and sorted for comparison
        pd.testing.assert_frame_equal(output_df.sort_values(by=['Course Code']).reset_index(drop=True), self.expected_output.sort_values(by=['Course Code']).reset_index(drop=True))

if __name__ == '__main__':
    unittest.main()