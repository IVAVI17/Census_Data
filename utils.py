import os
import pandas as pd

DATA_FOLDER = 'data'

def load_data():
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.XLSX')]
    data_frames = []
    for file in files:
        df = pd.read_excel(os.path.join(DATA_FOLDER, file))
        data_frames.append(df)
    return pd.concat(data_frames, ignore_index=True)

def get_top_languages_by_state(data, state_code):
    state_data = data[data['District Code'] == '000']
    state_data = state_data[state_data['State'] == state_code]
    top_languages = state_data.groupby('Mother tongue name')['Total'].sum().nlargest(3)
    return top_languages.reset_index()

def get_top_languages_by_district(data, state_code, district_code):
    district_data = data[data['District Code'] != '000']
    district_data = district_data[(district_data['State'] == state_code) & (district_data['District Code'] == district_code)]
    top_languages = district_data.groupby('Mother tongue name')['Total'].sum().nlargest(3)
    return top_languages.reset_index()
