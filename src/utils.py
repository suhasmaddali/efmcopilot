import os
from datetime import datetime
import pandas as pd
import streamlit as st

def find_latest_file(directory, prefix="ATD_Final_DSHBRD_BUF_SELLIN_"):

    latest_file = None
    latest_time = None

    for file in os.listdir(directory):
        if file.startswith(prefix):
            try:
                timestamp_str = file[len(prefix):].rstrip('.csv')
                file_time = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
                if latest_time is None or file_time > latest_time:
                    latest_file = os.path.join(directory, file)
                    latest_time = file_time
            except ValueError:
                continue

    return latest_file

@st.cache_data
def read_and_display_latest_file(directory, prefix="ATD_Final_DSHBRD_BUF_SELLIN_", encoding="latin-1"):

    data = None
    latest_file_path = find_latest_file(directory, prefix)
    if latest_file_path:
        print(f"Latest file found: {latest_file_path}")
        try:
            columns_used = [
                "Time_Period", 
                "Marketing Sub Code", 
                "Business Unit", 
                "End Cust Group PROD (EFM)", 
                "EC Customer Region", 
                "Total RSF Rev.", 
                "Total RSF Qty",
                "Actualized RSF Locked LM Rev.",
                "Actualized RSF Locked LM Qty",
                "Net B/S Qty (EFM)",
                "Net B/S Rev. (EFM)",
                "Opp EU In-Fcst Qty"
            ]

            # Define dtypes
            dtypes = {
                "Time_Period": "string",
                "Marketing Sub Code": "string",
                "Business Unit": "string",
                "End Cust Group PROD (EFM)": "string",
                "EC Customer Region": "string",
                "Total RSF Rev.": "float32",
                "Total RSF Qty": "float32",
                "Actualized RSF Locked LM Rev.": "float32",
                "Actualized RSF Locked LM Qty": "float32",
                "Net B/S Qty (EFM)": "float32",
                "Net B/S Rev. (EFM)": "float32",
                "Opp EU In-Fcst Qty": "float32"
            }

            data = pd.read_csv(
                latest_file_path, 
                encoding=encoding, 
                usecols=columns_used,
                dtype=dtypes
            )

        except Exception as e:
            print(f"Error reading the file: {e}")
    else:
        print("No matching files found.")

    return data
