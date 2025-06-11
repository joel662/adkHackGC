import unittest
import pandas as pd
import os
from plannedCourse import audit_sheet_file, audit_sheet_df, course_data, specific_cells, output_file, audit_cleaned_df
import re


class TestPlannedCourse(unittest.TestCase):

    def setUp(self):
        # Create dummy Audit Sheet.xlsx for testing
        self.audit_sheet_test_file = "Audit Sheet_test.xlsx"
        self.test_data = {
            0: ["COSC3106 (3CR)", "25SP"],
            1: ["COSC3127 (3CR)", "CR"],
            2: ["COSC1046 (3CR)", "21F"],
            3: ["COSC2000 (3CR)", "CR"],
            29: ["COSC4000", "CR"], # Test for specific cells
            33: ["COSC5000", "26FA"] # Test for specific cells
        }
        self.df = pd.DataFrame.from_dict(self.test_data, orient='index')
        self.df.to_excel(self.audit_sheet_test_file, header=False, index=False)

        # Create a temporary output file path
        self.temp_output_file = "temp_merged_data.csv"


    def tearDown(self):
        # Clean up the test file
        if os.path.exists(self.audit_sheet_test_file):
            os.remove(self.audit_sheet_test_file)

        # Clean up the temporary output file
        if os.path.exists(self.temp_output_file):
            os.remove(self.temp_output_file)



    def test_audit_sheet_loading(self):
        # Test if the audit sheet is loaded correctly
        df = pd.read_excel(self.audit_sheet_test_file, header=None)
        self.assertFalse(df.empty, "Audit sheet not loaded successfully")
        self.assertEqual(df.shape[0], 4, "Incorrect number of rows loaded") # Adjusted to reflect the test data
        self.assertEqual(df.shape[1], 2, "Incorrect number of columns loaded")  # Adjusted to reflect the test data

    def test_course_data_extraction(self):
        # Test course data extraction from audit sheet.
        # Re-initialize course_data to ensure it's clean for this test.
        course_data_test = []
        df = pd.read_excel(self.audit_sheet_test_file, header=None)
        num_rows, num_cols = df.shape
        for row_idx in range(num_rows):
            for col_idx in range(num_cols):
                cell_value = df.iloc[row_idx, col_idx]
                next_cell_value = df.iloc[row_idx, col_idx + 1] if col_idx + 1 < num_cols else None
                if pd.notna(cell_value):
                    match = re.match(r"([A-Z]+\d+|[A-Z]+\d+[A-Z]*)\s*\((\d+)CR\)", str(cell_value))
                    if match:
                        course_code, credits = match.groups()
                        term = next_cell_value if next_cell_value and re.match(r"\d{2}[A-Z]+", str(next_cell_value)) else None
                        status = "To be Registered" if next_cell_value != "CR" else "Completed"
                        if status == "To be Registered" or term:
                            credits = 0 if status == "To be Registered" else int(credits)
                            course_data_test.append([term, course_code, status, credits, "Predicted Term: " + str(term) if term else ""])
        self.assertEqual(len(course_data_test), 2, "Incorrect number of courses extracted")
        self.assertEqual(course_data_test[0][1], "COSC3106")
        self.assertEqual(course_data_test[0][2], "To be Registered")
        self.assertEqual(course_data_test[0][0], "25SP")
        self.assertEqual(course_data_test[1][1], "COSC1046")
        self.assertEqual(course_data_test[1][2], "To be Registered")
        self.assertEqual(course_data_test[1][0], "21F")


    def test_specific_cells_processing(self):

        course_data_test = []
        df = pd.read_excel(self.audit_sheet_test_file, header=None)
        specific_cells_test = [
            ("A30", "B30"),
            ("A34", "B34")
        ]

        for cell1, cell2 in specific_cells_test:
            row1, col1 = int(cell1[1:]) - 1, ord(cell1[0]) - ord('A')
            row2, col2 = int(cell2[1:]) - 1, ord(cell2[0]) - ord('A')

            cell_value1 = df.iloc[row1, col1]
            cell_value2 = df.iloc[row2, col2]

            if pd.notna(cell_value1):
                match = re.match(r"([A-Z]+\d+|[A-Z]+\d+[A-Z]*)", str(cell_value1))
                if match:
                    course_code = match.group(1)
                    credits = 3  # Assuming 3 credits for these specific cells
                    term = cell_value2 if cell_value2 and re.match(r"\d{2}[A-Z]+", str(cell_value2)) else None
                    status = "To be Registered" if cell_value2 != "CR" else "Completed"
                    if status == "To be Registered" or term:
                        credits = 0 if status == "To be Registered" else credits
                        course_data_test.append([term, course_code, status, credits, "Predicted Term: " + str(term) if term else ""])

        self.assertEqual(len(course_data_test), 2, "Incorrect number of specific cells processed")
        self.assertEqual(course_data_test[0][1], "COSC4000")
        self.assertEqual(course_data_test[0][2], "To be Registered")
        self.assertEqual(course_data_test[0][0], None)
        self.assertEqual(course_data_test[1][1], "COSC5000")
        self.assertEqual(course_data_test[1][2], "To be Registered")
        self.assertEqual(course_data_test[1][0], "26FA")



    def test_csv_output_creation(self):
        # Create a minimal test dataframe

        # Process audit sheet
        course_data_test = []
        df = pd.read_excel(self.audit_sheet_test_file, header=None)
        num_rows, num_cols = df.shape
        for row_idx in range(num_rows):
            for col_idx in range(num_cols):
                cell_value = df.iloc[row_idx, col_idx]
                next_cell_value = df.iloc[row_idx, col_idx + 1] if col_idx + 1 < num_cols else None
                if pd.notna(cell_value):
                    match = re.match(r"([A-Z]+\d+|[A-Z]+\d+[A-Z]*)\s*\((\d+)CR\)", str(cell_value))
                    if match:
                        course_code, credits = match.groups()
                        term = next_cell_value if next_cell_value and re.match(r"\d{2}[A-Z]+", str(next_cell_value)) else None
                        status = "To be Registered" if next_cell_value != "CR" else "Completed"
                        if status == "To be Registered" or term:
                            credits = 0 if status == "To be Registered" else int(credits)
                            course_data_test.append([term, course_code, status, credits, "Predicted Term: " + str(term) if term else ""])
        # Process specific cells
        specific_cells_test = [
            ("A30", "B30"),
            ("A34", "B34")
        ]

        for cell1, cell2 in specific_cells_test:
            row1, col1 = int(cell1[1:]) - 1, ord(cell1[0]) - ord('A')
            row2, col2 = int(cell2[1:]) - 1, ord(cell2[0]) - ord('A')

            cell_value1 = df.iloc[row1, col1]
            cell_value2 = df.iloc[row2, col2]

            if pd.notna(cell_value1):
                match = re.match(r"([A-Z]+\d+|[A-Z]+\d+[A-Z]*)", str(cell_value1))
                if match:
                    course_code = match.group(1)
                    credits = 3  # Assuming 3 credits for these specific cells
                    term = cell_value2 if cell_value2 and re.match(r"\d{2}[A-Z]+", str(cell_value2)) else None
                    status = "To be Registered" if cell_value2 != "CR" else "Completed"
                    if status == "To be Registered" or term:
                        credits = 0 if status == "To be Registered" else credits
                        course_data_test.append([term, course_code, status, credits, "Predicted Term: " + str(term) if term else ""])

        audit_cleaned_df_test = pd.DataFrame(course_data_test, columns=["Term", "Course Code", "Status", "Credits", "Notes"])
        audit_cleaned_df_test.to_csv(self.temp_output_file, index=False)

        self.assertTrue(os.path.exists(self.temp_output_file), "Output CSV not created")
        output_df = pd.read_csv(self.temp_output_file)
        self.assertFalse(output_df.empty, "Output CSV is empty")
        self.assertEqual(output_df.shape[0], 4, "Incorrect number of rows in output CSV") # Adjust expected rows to the test data
        self.assertEqual(output_df.shape[1], 5, "Incorrect number of columns in output CSV") # Adjust expected rows to the test data


if __name__ == "__main__":
    unittest.main()