import pandas as pd
import logging

def load_abend_data(filepath):
    logging.debug(f"Loading abend data from {filepath}")
    return pd.read_excel(filepath)
