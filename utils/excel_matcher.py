import pandas as pd

class ExcelMatcher:
    def __init__(self, excel_path):
        self.excel_path = excel_path

    def compare_and_generate_list(self, detected_rolls):
        # Load your Master Excel sheet
        df = pd.read_excel(self.excel_path)
        
        # Ensure column name matches your Excel (e.g., 'CRN' or 'Roll No')
        # We convert to string to ensure comparison works
        df['CRN_str'] = df['CRN'].astype(str).str.strip()
        
        # Create the Status column
        df['Status'] = df['CRN_str'].apply(lambda x: 'Present' if x in detected_rolls else 'Absent')
        
        # Drop the helper column and return as list of dicts
        final_df = df.drop(columns=['CRN_str'])
        return final_df.to_dict(orient='records')
