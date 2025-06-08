import unittest
import pandas as pd
import os
from unittest.mock import patch
import re

# Assuming the code to be tested is saved in a file named 'merge_data.py'
# and the following import is adjusted accordingly:
# from merge_data import ...  (or whatever name the file is)

# Create dummy excel files for testing
def create_dummy_audit_sheet(filename="Audit Sheet.xlsx", data=None):
    if data is None:
        data = [
            ["COSC3106 (3CR)", "25SP"],
            ["COSC3127 (3CR)", "CR"],
            ["COSC1046 (3CR)", "21F"],
            ["COSC2000 (3CR)", "CR"]
        ]
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False, header=False)

def create_dummy_audit_sheet_with_specific_cells(filename="Audit Sheet.xlsx", data=None):
    if data is None:
        data = [
            ["", "", "", "", "", "", "COSC3106", "25SP"],
            ["", "", "", "", "", "", "", "CR"],
            ["", "", "", "", "", "", "COSC1046", "21F"],
            ["", "", "", "", "", "", "", "CR"]
        ]
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False, header=False)

def create_dummy_past_courses(filename="past_courses.xlsx", data=None):
    if data is None:
        data = [
            ["Term", "Course Code", "Course Name", "Grade", "Credit"],
            ["21F", "COSC1046", "Introduction to Computer Science I", "91", 3]
        ]
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False, header=True)


def remove_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


class TestMergeData(unittest.TestCase):
    def setUp(self):
        # Create dummy files before each test
        self.audit_sheet_file = "Audit Sheet.xlsx"
        self.past_courses_file = "past_courses.xlsx"
        self.output_file = "plannedCourse.csv"
        remove_file(self.audit_sheet_file)
        remove_file(self.past_courses_file)
        remove_file(self.output_file)


    def tearDown(self):
        # Remove dummy files after each test
        remove_file(self.audit_sheet_file)
        remove_file(self.past_courses_file)
        remove_file(self.output_file)

    def test_audit_sheet_extraction_normal_case(self):
        create_dummy_audit_sheet(self.audit_sheet_file)

        # Execute the code to generate the CSV
        exec(open("code.py").read())
        # Assert that the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and perform assertions
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 2)  # Expecting two entries
        self.assertTrue(output_df["Course Code"].isin(["COSC3106", "COSC1046"]).all())
        self.assertTrue(output_df["Status"].isin(["To be Registered", "To be Registered"]).all())
        self.assertTrue(output_df["Credits"].isin([0, 0]).all())

    def test_audit_sheet_extraction_with_specific_cells(self):
         create_dummy_audit_sheet_with_specific_cells(self.audit_sheet_file)

         # Execute the code to generate the CSV
         exec(open("code.py").read())

         # Assert that the output file exists
         self.assertTrue(os.path.exists(self.output_file))

         # Read the output file and perform assertions
         output_df = pd.read_csv(self.output_file)
         self.assertEqual(len(output_df), 2)
         self.assertTrue(output_df["Course Code"].isin(["COSC3106", "COSC1046"]).all())
         self.assertTrue(output_df["Status"].isin(["To be Registered", "To be Registered"]).all())
         self.assertTrue(output_df["Credits"].isin([0, 0]).all())

    def test_audit_sheet_extraction_no_matches(self):
        # Create an audit sheet with no matching course codes
        create_dummy_audit_sheet(self.audit_sheet_file, [["MATH1000 (3CR)", "21F"]])

        # Execute the code
        exec(open("code.py").read())

        # Check if the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and check the content.
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 1)
        self.assertTrue(output_df["Course Code"].isin(["MATH1000"]).all())
        self.assertEqual(output_df["Status"][0], "To be Registered")


    def test_audit_sheet_extraction_empty_audit_sheet(self):
        # Create an empty audit sheet
        create_dummy_audit_sheet(self.audit_sheet_file, [])

        # Execute the code
        exec(open("code.py").read())

        # Check if the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and check the content.
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 0)

    def test_audit_sheet_extraction_missing_term(self):
        create_dummy_audit_sheet(self.audit_sheet_file, [["COSC3106 (3CR)", None]])

        # Execute the code
        exec(open("code.py").read())

        # Assert that the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and perform assertions
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df["Term"][0], None)
        self.assertEqual(output_df["Course Code"][0], "COSC3106")
        self.assertEqual(output_df["Status"][0], "To be Registered")
        self.assertEqual(output_df["Credits"][0], 0)
        self.assertEqual(output_df["Notes"][0], "Predicted Term: None")

    def test_audit_sheet_extraction_term_is_CR(self):
        create_dummy_audit_sheet(self.audit_sheet_file, [["COSC3106 (3CR)", "CR"]])

        # Execute the code
        exec(open("code.py").read())

        # Assert that the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and perform assertions
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 1)
        self.assertEqual(output_df["Term"][0], None)
        self.assertEqual(output_df["Course Code"][0], "COSC3106")
        self.assertEqual(output_df["Status"][0], "Completed")
        self.assertEqual(output_df["Credits"][0], 0)

    def test_audit_sheet_extraction_with_invalid_course_code_format(self):
        create_dummy_audit_sheet(self.audit_sheet_file, [["INVALID-CODE (3CR)", "21F"]])
        exec(open("code.py").read())

        self.assertTrue(os.path.exists(self.output_file))

        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 0)  # Expecting no entries as invalid course code

    def test_audit_sheet_extraction_missing_credits(self):
        create_dummy_audit_sheet(self.audit_sheet_file, [["COSC3106", "21F"]])
        exec(open("code.py").read())

        self.assertTrue(os.path.exists(self.output_file))

        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 0) # Expecting no entries

    def test_audit_sheet_extraction_no_neighboring_cell(self):
         create_dummy_audit_sheet(self.audit_sheet_file, [["COSC3106 (3CR)"]])
         exec(open("code.py").read())

         self.assertTrue(os.path.exists(self.output_file))

         output_df = pd.read_csv(self.output_file)
         self.assertEqual(len(output_df), 1)
         self.assertEqual(output_df["Term"][0], None)
         self.assertEqual(output_df["Course Code"][0], "COSC3106")
         self.assertEqual(output_df["Status"][0], "To be Registered")
         self.assertEqual(output_df["Credits"][0], 0)

    def test_specific_cells_extraction_no_matches(self):
        create_dummy_audit_sheet(self.audit_sheet_file, [["", "", "", "", "", "", "MATH1000", "25SP"]])

        # Execute the code to generate the CSV
        exec(open("code.py").read())
        # Assert that the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and perform assertions
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 1)  # Expecting one entry
        self.assertTrue(output_df["Course Code"].isin(["MATH1000"]).all())
        self.assertEqual(output_df["Status"][0], "To be Registered")
        self.assertEqual(output_df["Term"][0], "25SP")
        self.assertEqual(output_df["Credits"][0], 0)

    def test_specific_cells_extraction_term_CR(self):
        create_dummy_audit_sheet(self.audit_sheet_file, [["", "", "", "", "", "", "MATH1000", "CR"]])

        # Execute the code to generate the CSV
        exec(open("code.py").read())
        # Assert that the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and perform assertions
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 1)  # Expecting one entry
        self.assertTrue(output_df["Course Code"].isin(["MATH1000"]).all())
        self.assertEqual(output_df["Status"][0], "Completed")
        self.assertEqual(output_df["Term"][0], None)
        self.assertEqual(output_df["Credits"][0], 3)

    def test_specific_cells_extraction_invalid_course_code(self):
        create_dummy_audit_sheet(self.audit_sheet_file, [["", "", "", "", "", "", "INVALID-CODE", "25SP"]])

        # Execute the code to generate the CSV
        exec(open("code.py").read())
        # Assert that the output file exists
        self.assertTrue(os.path.exists(self.output_file))

        # Read the output file and perform assertions
        output_df = pd.read_csv(self.output_file)
        self.assertEqual(len(output_df), 0) # Expecting no entries

if __name__ == "__main__":
    unittest.main()