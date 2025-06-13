"""
There will be two inputs givenm Audit Sheet.xlsx and past_courses.xlsx.
The goal is to merge the two files based on the Course Code column.
The output will be a new Excel file with the merged data.

Ensure the CSV includes all necessary columns (e.g., course code, status, term, credits, and any notes).
The final output should be saved as a new Excel file named merged_data.xlsx.

The input from past_courses.xlsx will be in the following format:
Term	Course Code	Course Name	Grade	Credit
21F	COSC1046	Introduction to Computer Science I	91	3
The input from Audit Sheet.xlsx will be in the following format:
COSC3106 (3CR)	25SP
COSC3127 (3CR)	CR

ignore the ones with CR in the term column

Expected output:
course code, status, term, credits, and any notes
COSC1046, Complete, 21F, 3,
COSC3106,To be registred, 25SP, 3,
"""
import pandas as pd
import re


audit_sheet_file = "Audit Sheet.xlsx"

# Load audit sheet data
audit_sheet_df = pd.read_excel(audit_sheet_file, header=None)

# Extract relevant course data from the audit sheet (A1 to H35), checking every cell and its right neighbor
course_data = []
num_rows, num_cols = audit_sheet_df.shape
for row_idx in range(num_rows):
    for col_idx in range(num_cols):
        cell_value = audit_sheet_df.iloc[row_idx]#added an error here, it should be iloc[row_idx, col_idx]
        next_cell_value = audit_sheet_df.iloc[row_idx, col_idx + 1] if col_idx + 1 < num_cols else None
        
        if pd.notna(cell_value):
            match = re.match(r"([A-Z]+\d+|[A-Z]+\d+[A-Z]*)\s*\((\d+)CR\)", str(cell_value))
            if match:
                course_code, credits = match.groups()
                term = next_cell_value if next_cell_value and re.match(r"\d{2}[A-Z]+", str(next_cell_value)) else None
                status = "To be Registered" if next_cell_value != "CR" else "Completed"
                if status == "To be Registered" or term:
                    credits = 0 if status == "To be Registered" else int(credits)
                    course_data.append([term, course_code, status, credits, "Predicted Term: " + str(term) if term else ""])

print("Processing specific cells...")
for cell1, cell2 in specific_cells:
    row1, col1 = int(cell1[1:]) - 1, ord(cell1[0]) - ord('A')
    row2, col2 = int(cell2[1:]) - 1, ord(cell2[0]) - ord('A')
    
    cell_value1 = audit_sheet_df.iloc[row1, col1]
    cell_value2 = audit_sheet_df.iloc[row2, col2]
    
    print(f"Processing cells {cell1} and {cell2}: {cell_value1}, {cell_value2}")
    
    if pd.notna(cell_value1):
        match = re.match(r"([A-Z]+\d+|[A-Z]+\d+[A-Z]*)", str(cell_value1))
        if match:
            course_code = match.group(1)
            credits = 3  # Assuming 3 credits for these specific cells
            term = cell_value2 if cell_value2 and re.match(r"\d{2}[A-Z]+", str(cell_value2)) else None
            status = "To be Registered" if cell_value2 != "CR" else "Completed"
            if status == "To be Registered" or term:
                credits = 0 if status == "To be Registered" else credits
                course_data.append([term, course_code, status, credits, "Predicted Term: " + str(term) if term else ""])
                print(f"Added: {term}, {course_code}, {status}, {credits}, {'Predicted Term: ' + str(term) if term else ''}")
            else:
                print(f"Error: Cell {cell1} and {cell2} not added correctly")
        else:
            print(f"Error: Cell {cell1} does not match the expected format")
    else:
        print(f"Error: Cell {cell1} is empty")
print("Finished processing specific cells.")

# Convert audit data to DataFrame
audit_cleaned_df = pd.DataFrame(course_data, columns=["Term", "Course Code", "Status", "Credits", "Notes"])

output_file = "plannedCourse.csv"
audit_cleaned_df.to_csv(output_file, index=False)