import pandas as pd

def load_abend_data(file_path):
    # Load the abend data from the provided Excel file
    abend_data = pd.read_excel(file_path)
    return abend_data
