from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class RequestModel(BaseModel):
    state_name: str
    num_languages: int
    
class DistrictRequestModel(BaseModel):
    state_name: str
    district_name: str
    num_languages: int

@app.post("/most_spoken_languages/")
async def most_spoken_languages(request: RequestModel):
    state_name = request.state_name
    num_languages = request.num_languages
    file_name = state_name.replace(" ", "_") + ".xlsx"
    file_path = os.path.join("data", file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        df = pd.read_excel(file_path, skiprows=3)
        
        df.columns = [
            "Table name", "State code", "District code", "Town code", "Area name",
            "Mother tongue code", "Mother tongue name", "Unnamed: 7", "Unnamed: 8",
            "Unnamed: 9", "Rural P", "Unnamed: 11", "Unnamed: 12",
            "Urban P", "Unnamed: 14", "Unnamed: 15"
        ]

        df.columns = df.columns.str.strip()
        
        df['District code'] = df['District code'].astype(str)
        df_filtered = df[df['District code'] == '0.0']
        
        if 'Mother tongue name' not in df_filtered.columns or 'Urban P' not in df_filtered.columns:
            raise HTTPException(status_code=500, detail="'Mother tongue name' or 'Urban P' column not found")

        df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip().str.lower()

        # df_grouped = df_filtered[['Mother tongue name', 'Urban P']].groupby('Mother tongue name').sum().reset_index()
        
        df_filtered = df_filtered.sort_values(by='Urban P', ascending=False)
        
        df_reversed = df_filtered.iloc[::-1]
        
        df_deduped_reversed = df_reversed.drop_duplicates(subset=['Mother tongue name'], keep='first')
        
        df_filtered = df_deduped_reversed.iloc[::-1]
        
        df_grouped = df_filtered[['Mother tongue name', 'Urban P']]



        df_sorted = df_grouped.sort_values(by='Urban P', ascending=False)

        top_languages = df_sorted.head(num_languages).to_dict(orient='records')

        return {"state": state_name, "top_languages": top_languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_district_code(state_name: str, district_name: str) -> str:
    census_file_path = r"./District_Codes.xlsx"
    if not os.path.exists(census_file_path):
        raise HTTPException(status_code=404, detail="Census file not found")

    census_df = pd.read_excel(census_file_path)
    
    print("Columns in census file:", census_df.columns.tolist())

    census_df.columns = census_df.columns.str.replace('\n', ' ').str.strip()
    
    expected_columns = ['State', 'State Code', 'District Code', 'District Name']
    if not all(col in census_df.columns for col in expected_columns):
        raise HTTPException(status_code=500, detail=f"500: Expected columns {expected_columns} not found in census file. Actual columns: {census_df.columns.tolist()}")

    row = census_df[(census_df['State'].str.strip().str.lower() == state_name.strip().lower()) &
                    (census_df['District Name'].str.strip().str.lower() == district_name.strip().lower())]

    if row.empty:
        raise HTTPException(status_code=404, detail="District not found in census file")

    district_code = row.iloc[0]['District Code']
    return str(district_code)

@app.post("/district_languages/")
async def district_languages(request: DistrictRequestModel):
    state_name = request.state_name
    district_name = request.district_name
    num_languages = request.num_languages
    file_name = state_name.replace(" ", "_") + ".xlsx"
    file_path = os.path.join("data", file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="State file not found")

    try:
        district_code = get_district_code(state_name, district_name)
        print(f"District code for {district_name} in {state_name} is {district_code}")

        df = pd.read_excel(file_path, skiprows=3)
        
        df.columns = [
            "Table name", "State code", "District code", "Town code", "Area name",
            "Mother tongue code", "Mother tongue name", "Unnamed: 7", "Unnamed: 8",
            "Unnamed: 9", "Rural P", "Unnamed: 11", "Unnamed: 12",
            "Urban P", "Unnamed: 14", "Unnamed: 15"
        ]

        # Print dataframe for debugging
        print("Dataframe after reading the file:")
        print(df.head())
        
        print(df.dtypes)

        df.columns = df.columns.str.strip()
        
        df['District code'] = pd.to_numeric(df['District code'], errors='coerce')

        district_code = float(district_code)

        df_filtered = df[df['District code'] == district_code]

        print(f"Dataframe after filtering 'District code' == '{district_code}':")
        print(df_filtered.head())

        if 'Mother tongue name' not in df_filtered.columns or 'Urban P' not in df_filtered.columns:
            raise HTTPException(status_code=500, detail="'Mother tongue name' or 'Urban P' column not found")

        df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip().str.lower()

        print("Mother tongue names and Totals before grouping:")
        print(df_filtered[['Mother tongue name', 'Urban P']])

        df_grouped = df_filtered[['Mother tongue name', 'Urban P']].groupby('Mother tongue name').sum().reset_index()

        print("Dataframe after grouping by 'Mother tongue name':")
        print(df_grouped.head())

        df_sorted = df_grouped.sort_values(by='Urban P', ascending=False)

        top_languages = df_sorted.head(num_languages).to_dict(orient='records')

        return {"state": state_name, "district": district_name, "top_languages": top_languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/generate_top_languages_report/")
async def generate_top_languages_report():
    data_dir = "data"
    num_languages = 4
    all_states_top_languages = []

    try:
        for file_name in os.listdir(data_dir):
            if file_name.endswith(".XLSX"):
                state_name = file_name.replace("_", " ").replace(".XLSX", "")
                file_path = os.path.join(data_dir, file_name)
                
                df = pd.read_excel(file_path, skiprows=3)
                
                df.columns = [
                    "Table name", "State code", "District code", "Town code", "Area name",
                    "Mother tongue code", "Mother tongue name", "Unnamed: 7", "Unnamed: 8",
                    "Unnamed: 9", "Rural P", "Unnamed: 11", "Unnamed: 12",
                    "Urban P", "Unnamed: 14", "Unnamed: 15"
                ]

                df.columns = df.columns.str.strip()
                
                df['District code'] = df['District code'].astype(str)
                df_filtered = df[df['District code'] == '0.0']
                
                if 'Mother tongue name' not in df_filtered.columns or 'Urban P' not in df_filtered.columns:
                    continue

                df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip().str.lower()

               
                df_filtered = df_filtered.sort_values(by='Urban P', ascending=False)
                
                df_reversed = df_filtered.iloc[::-1]

                df_deduped_reversed = df_reversed.drop_duplicates(subset=['Mother tongue name'], keep='first')
                
                df_filtered = df_deduped_reversed.iloc[::-1]
                
                df_grouped = df_filtered[['Mother tongue name', 'Urban P']]
                 
                df_sorted = df_grouped.sort_values(by='Urban P', ascending=False)

                top_languages = df_sorted.head(num_languages).to_dict(orient='records')

                for lang in top_languages:
                    all_states_top_languages.append({
                        "State": state_name,
                        "Mother tongue name": lang["Mother tongue name"],
                        "Urban P": lang["Urban P"]
                    })
        
        if not all_states_top_languages:
            raise HTTPException(status_code=500, detail="No data found for any state")
        
        report_df = pd.DataFrame(all_states_top_languages)
        output_file_path = os.path.join(data_dir, "Top_3_Languages_Indian_States.xlsx")
        report_df.to_excel(output_file_path, index=False)

        return {"message": "Report generated successfully", "file_path": output_file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/generate_top_languages_report1/")
async def generate_top_languages_report():
    data_dir = "data"
    num_languages = 4
    all_states_top_languages = []

    try:
        for file_name in os.listdir(data_dir):
            if file_name.endswith(".XLSX"):
                state_name = file_name.replace("_", " ").replace(".XLSX", "")
                file_path = os.path.join(data_dir, file_name)
                
                df = pd.read_excel(file_path, skiprows=3)
                
                df.columns = [
                    "Table name", "State code", "District code", "Town code", "Area name",
                    "Mother tongue code", "Mother tongue name", "Unnamed: 7", "Unnamed: 8",
                    "Unnamed: 9", "Rural P", "Unnamed: 11", "Unnamed: 12",
                    "Urban P", "Unnamed: 14", "Unnamed: 15"
                ]

                df.columns = df.columns.str.strip()
                
                df['District code'] = df['District code'].astype(str)
                df_filtered = df[df['District code'] == '0.0']
                
                if 'Mother tongue name' not in df_filtered.columns or 'Urban P' not in df_filtered.columns:
                    continue

                df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip().str.lower()

                df_filtered = df_filtered.sort_values(by='Urban P', ascending=False)
                df_reversed = df_filtered.iloc[::-1]
                df_deduped_reversed = df_reversed.drop_duplicates(subset=['Mother tongue name'], keep='first')
                df_filtered = df_deduped_reversed.iloc[::-1]
                
                df_grouped = df_filtered[['Mother tongue name', 'Urban P']]
                df_sorted = df_grouped.sort_values(by='Urban P', ascending=False)
                top_languages = df_sorted.head(num_languages).to_dict(orient='records')

                state_data = {"State": state_name}
                total_speakers = 0

                for lang in top_languages:
                    state_data[lang["Mother tongue name"]] = lang["Urban P"]
                    total_speakers += lang["Urban P"]

                state_data["Total"] = total_speakers
                all_states_top_languages.append(state_data)

                # Adding percentage row for the state
                percentage_data = {"State": state_name + " (Percentage)"}
                for lang in top_languages:
                    percentage_data[lang["Mother tongue name"]] = f"{(lang['Urban P'] / total_speakers) * 100:.2f}%"

                all_states_top_languages.append(percentage_data)
        
        if not all_states_top_languages:
            raise HTTPException(status_code=500, detail="No data found for any state")
        
        report_df = pd.DataFrame(all_states_top_languages)

        # Rearrange columns to ensure "Total" is the last column
        cols = [col for col in report_df.columns if col != "Total"] + ["Total"]
        report_df = report_df[cols]

        output_file_path = os.path.join(data_dir, "Top_4_Languages_Indian_States.xlsx")
        report_df.to_excel(output_file_path, index=False)

        return {"message": "Report generated successfully", "file_path": output_file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
# @app.get("/generate_town_languages_report/")
# async def generate_town_languages_report():
#     data_dir = "dataa"
#     num_languages = 3
#     all_towns_top_languages = []

#     try:
#         for file_name in os.listdir(data_dir):
#             if file_name.endswith(".XLSX"):
#                 state_name = file_name.replace("_", " ").replace(".XLSX", "")
#                 file_path = os.path.join(data_dir, file_name)
                
#                 df = pd.read_excel(file_path, skiprows=3)
                
#                 df.columns = [
#                     "Table name", "State code", "District code", "Town code", "Area name",
#                     "Mother tongue code", "Mother tongue name", "Total P", "Total M", "Total F",
#                     "Rural P", "Rural M", "Rural F",
#                     "Urban P", "Urban M", "Urban F"
#                 ]

#                 df.columns = df.columns.str.strip()

#                 # Filter out rows where District code is '0.0' which corresponds to the entire state
#                 df['District code'] = pd.to_numeric(df['District code'], errors='coerce')
#                 df['Town code'] = pd.to_numeric(df['Town code'], errors='coerce')
#                 df_filtered = df[df['District code'] != 0]

#                 if 'Mother tongue name' not in df_filtered.columns or 'Total P' not in df_filtered.columns:
#                     continue

#                 df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip().str.lower()

#                 # Group by District code and Town code, then find top languages
#                 grouped = df_filtered.groupby(['District code', 'Town code', 'Area name', 'Mother tongue name']).agg({
#                     'Total P': 'sum',
#                     'Total M': 'sum',
#                     'Total F': 'sum'
#                 }).reset_index()

#                 sorted_grouped = grouped.sort_values(by='Total P', ascending=False)

#                 top_languages = sorted_grouped.groupby(['District code', 'Town code', 'Area name']).head(num_languages)

#                 for _, row in top_languages.iterrows():
#                     all_towns_top_languages.append({
#                         "State": state_name,
#                         "District Code": row['District code'],
#                         "Town Code": row['Town code'],
#                         "Town": row['Area name'],
#                         "Language": row['Mother tongue name'],
#                         "Total Population": row['Total P'],
#                         "Male Population": row['Total M'],
#                         "Female Population": row['Total F']
#                     })

#         if not all_towns_top_languages:
#             raise HTTPException(status_code=500, detail="No data found for any town")

#         report_df = pd.DataFrame(all_towns_top_languages)
#         output_file_path = os.path.join(data_dir, "Top_3_Languages_Indian_Towns.xlsx")
#         report_df.to_excel(output_file_path, index=False)

#         return {"message": "Report generated successfully", "file_path": output_file_path}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/generate_town_languages_report/")
# async def generate_town_languages_report():
#     data_dir = "data"
#     num_languages = 4
#     all_towns_top_languages = []

#     def keep_second_occurrence(df, subset):
#         df['occurrence'] = df.groupby(subset).cumcount() + 1
#         second_occurrence_df = df[df['occurrence'] == 2].drop(columns=['occurrence'])
#         return second_occurrence_df

#     try:
#         for file_name in os.listdir(data_dir):
#             if file_name.endswith(".XLSX"):
#                 state_name = file_name.replace("_", " ").replace(".XLSX", "")
#                 file_path = os.path.join(data_dir, file_name)
                
#                 df = pd.read_excel(file_path, skiprows=3)
                
#                 df.columns = [
#                     "Table name", "State code", "District code", "Town code", "Area name",
#                     "Mother tongue code", "Mother tongue name", "Total P", "Total M", "Total F",
#                     "Rural P", "Rural M", "Rural F",
#                     "Urban P", "Urban M", "Urban F"
#                 ]

#                 df.columns = df.columns.str.strip()

#                 # Filter out rows where District code is '0.0' which corresponds to the entire state
#                 df['District code'] = pd.to_numeric(df['District code'], errors='coerce')
#                 df['Town code'] = pd.to_numeric(df['Town code'], errors='coerce')
#                 df_filtered = df[df['District code'] != 0]

#                 if 'Mother tongue name' not in df_filtered.columns or 'Total P' not in df_filtered.columns:
#                     continue

#                 df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip().str.lower()

#                 # Keep only the second occurrence of each Mother tongue name within each District code and Town code
#                 df_filtered = keep_second_occurrence(df_filtered, ['Mother tongue name', 'District code', 'Town code'])

#                 # Group by District code
#                 grouped_by_district = df_filtered.groupby('District code')

#                 for district_code, district_df in grouped_by_district:
#                     # Find the District Name (Area name where Town code is 0.0)
#                     district_name = district_df[district_df['Town code'] == 0.0]['Area name'].values[0] if not district_df[district_df['Town code'] == 0.0].empty else None
                    
#                     # Group by Town code within the district
#                     grouped_by_town = district_df.groupby(['Town code', 'Area name'])

#                     for (town_code, town_name), town_df in grouped_by_town:
#                         # Skip the district-level row (where Town code is 0.0)
#                         # if town_code == 0.0:
#                         #     continue

#                         # Find the top languages within the town
#                         town_grouped = town_df.groupby('Mother tongue name').agg({
#                             'Total P': 'sum',
#                             'Total M': 'sum',
#                             'Total F': 'sum'
#                         }).reset_index()

#                         sorted_town_grouped = town_grouped.sort_values(by='Total P', ascending=False)

#                         top_languages = sorted_town_grouped.head(num_languages)

#                         for _, row in top_languages.iterrows():
#                             all_towns_top_languages.append({
#                                 "State": state_name,
#                                 "District Name": district_name,
#                                 "Town": town_name,
#                                 "Language": row['Mother tongue name'],
#                                 "Total Population": row['Total P'],
#                                 "Male Population": row['Total M'],
#                                 "Female Population": row['Total F']
#                             })

#         if not all_towns_top_languages:
#             raise HTTPException(status_code=500, detail="No data found for any town")

#         report_df = pd.DataFrame(all_towns_top_languages)


#         output_file_path = os.path.join(data_dir, "Top_3_Languages_Indian_Towns.xlsx")
#         report_df.to_excel(output_file_path, index=False)

#         return {"message": "Report generated successfully", "file_path": output_file_path}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate_town_languages_report/")
async def generate_town_languages_report():
    data_dir = "data"
    num_languages = 4
    all_towns_top_languages = []

    def keep_second_occurrence(df, subset):
        df['occurrence'] = df.groupby(subset).cumcount() + 1
        second_occurrence_df = df[df['occurrence'] == 2].drop(columns=['occurrence'])
        return second_occurrence_df

    def clean_town_name(name):
        if isinstance(name, str):
            return name.split(' (')[0].strip().lower()
        return name

    try:
        # Load pincode data
        pincode_df = pd.read_csv(os.path.join(data_dir, "Updated_Pincode.csv"))
        pincode_df['Office Name'] = pincode_df['Office Name'].apply(clean_town_name)
        pincode_map = pincode_df.groupby('Office Name')['Pincode'].apply(list).to_dict()

        for file_name in os.listdir(data_dir):
            if file_name.endswith(".XLSX"):
                state_name = file_name.replace("_", " ").replace(".XLSX", "")
                file_path = os.path.join(data_dir, file_name)

                df = pd.read_excel(file_path, skiprows=3)

                df.columns = [
                    "Table name", "State code", "District code", "Town code", "Area name",
                    "Mother tongue code", "Mother tongue name", "Total P", "Total M", "Total F",
                    "Rural P", "Rural M", "Rural F",
                    "Urban P", "Urban M", "Urban F"
                ]

                df.columns = df.columns.str.strip()

                # Filter out rows where District code is '0.0' which corresponds to the entire state
                df['District code'] = pd.to_numeric(df['District code'], errors='coerce')
                df['Town code'] = pd.to_numeric(df['Town code'], errors='coerce')
                df_filtered = df[df['District code'] != 0]

                if 'Mother tongue name' not in df_filtered.columns or 'Total P' not in df_filtered.columns:
                    continue

                df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip().str.lower()

                # Keep only the second occurrence of each Mother tongue name within each District code and Town code
                df_filtered = keep_second_occurrence(df_filtered, ['Mother tongue name', 'District code', 'Town code'])

                # Group by District code
                grouped_by_district = df_filtered.groupby('District code')

                for district_code, district_df in grouped_by_district:
                    # Find the District Name (Area name where Town code is 0.0)
                    district_name = district_df[district_df['Town code'] == 0.0]['Area name'].values[0] if not district_df[district_df['Town code'] == 0.0].empty else None

                    # Group by Town code within the district
                    grouped_by_town = district_df.groupby(['Town code', 'Area name'])

                    for (town_code, town_name), town_df in grouped_by_town:
                        # Find the top languages within the town
                        town_grouped = town_df.groupby('Mother tongue name').agg({
                            'Total P': 'sum',
                            'Total M': 'sum',
                            'Total F': 'sum'
                        }).reset_index()

                        sorted_town_grouped = town_grouped.sort_values(by='Total P', ascending=False)

                        top_languages = sorted_town_grouped.head(num_languages)

                        cleaned_town_name = clean_town_name(town_name)
                        pincodes = pincode_map.get(cleaned_town_name, [])

                        for _, row in top_languages.iterrows():
                            all_towns_top_languages.append({
                                "State": state_name,
                                "District Name": district_name,
                                "Town": town_name,
                                "Language": row['Mother tongue name'],
                                "Total Population": row['Total P'],
                                "Male Population": row['Total M'],
                                "Female Population": row['Total F'],
                                "Pincode": pincodes
                            })

        if not all_towns_top_languages:
            raise HTTPException(status_code=500, detail="No data found for any town")

        report_df = pd.DataFrame(all_towns_top_languages)

        output_file_path = os.path.join(data_dir, "Top_4_Languages_Indian_Towns_with_Pincode.xlsx")
        report_df.to_excel(output_file_path, index=False)

        return {"message": "Report generated successfully", "file_path": output_file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LanguageRequestModel(BaseModel):
    state_name: str
    num_languages: int

# @app.post("/top_languages/")
# async def top_languages(request: LanguageRequestModel):
#     state_name = request.state_name
#     num_languages = request.num_languages
#     file_name = state_name.replace(" ", "_") + ".xlsx"
#     file_path = os.path.join("data1", file_name)

#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="File not found")

#     try:
#         # Read the Excel file from the 7th row
#         df = pd.read_excel(file_path, skiprows=5)
#         df.columns = df.columns.str.strip()  # Strip any extra spaces in column names

#         # Extracting total speakers of languages
#         total_speakers_df = df.iloc[:, [1, 3, 4]].dropna()
#         total_speakers_df.columns = ['State name', 'Language', 'Persons']

#         # Extracting first subsidiary languages
#         first_subsidiary_df = df.iloc[:, [8, 9]].dropna()
#         first_subsidiary_df.columns = ['Language', 'Persons']

#         # Extracting second subsidiary languages
#         second_subsidiary_df = df.iloc[:, [13, 14]].dropna()
#         second_subsidiary_df.columns = ['Language', 'Persons']

#         # Sorting and selecting top languages
#         total_speakers_top = total_speakers_df.sort_values(by='Persons', ascending=False).head(num_languages).to_dict(orient='records')
#         first_subsidiary_top = first_subsidiary_df.sort_values(by='Persons', ascending=False).head(num_languages).to_dict(orient='records')
#         second_subsidiary_top = second_subsidiary_df.sort_values(by='Persons', ascending=False).head(num_languages).to_dict(orient='records')

#         return {
#             "state": state_name,
#             "top_languages": total_speakers_top,
#             "top_first_subsidiary_languages": first_subsidiary_top,
#             "top_second_subsidiary_languages": second_subsidiary_top
#         }
#     except KeyError as e:
#         raise HTTPException(status_code=500, detail=f"Column error: {str(e)}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


def process_file(file_path: str, num_languages: int):
    try:
        # Read the Excel file from the 6th row (skiprows=5)
        df = pd.read_excel(file_path, skiprows=5)
        df.columns = df.columns.str.strip()  # Strip any extra spaces in column names

        # Extracting total speakers of languages
        total_speakers_df = df.iloc[:, [1, 3, 4]].dropna()
        total_speakers_df.columns = ['State name', 'Language', 'Persons']

        # Extracting first subsidiary languages
        first_subsidiary_df = df.iloc[:, [8, 9]].dropna()
        first_subsidiary_df.columns = ['Language', 'Persons']

        # Extracting second subsidiary languages
        second_subsidiary_df = df.iloc[:, [13, 14]].dropna()
        second_subsidiary_df.columns = ['Language', 'Persons']

        # Convert languages to lowercase
        total_speakers_df['Language'] = total_speakers_df['Language'].str.lower()
        first_subsidiary_df['Language'] = first_subsidiary_df['Language'].str.lower()
        second_subsidiary_df['Language'] = second_subsidiary_df['Language'].str.lower()

        # Ensuring unique languages with the highest number of speakers
        total_speakers_df = total_speakers_df.groupby('Language', as_index=False).agg({'Persons': 'max'})
        first_subsidiary_df = first_subsidiary_df.groupby('Language', as_index=False).agg({'Persons': 'max'})
        second_subsidiary_df = second_subsidiary_df.groupby('Language', as_index=False).agg({'Persons': 'max'})

        # Sorting and selecting top languages
        total_speakers_top = total_speakers_df.sort_values(by='Persons', ascending=False).head(num_languages)
        first_subsidiary_top = first_subsidiary_df.sort_values(by='Persons', ascending=False).head(num_languages)
        second_subsidiary_top = second_subsidiary_df.sort_values(by='Persons', ascending=False).head(num_languages)

        return total_speakers_top, first_subsidiary_top, second_subsidiary_top
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Column error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/top_languages/")
async def top_languages(request: LanguageRequestModel):
    state_name = request.state_name
    num_languages = request.num_languages
    file_name = state_name.replace(" ", "_") + ".xlsx"
    file_path = os.path.join("data1", file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        total_speakers_top, first_subsidiary_top, second_subsidiary_top = process_file(file_path, num_languages)

        return {
            "state": state_name,
            "top_languages": total_speakers_top.to_dict(orient='records'),
            "top_first_subsidiary_languages": first_subsidiary_top.to_dict(orient='records'),
            "top_second_subsidiary_languages": second_subsidiary_top.to_dict(orient='records')
        }
    except HTTPException as e:
        raise e

@app.get("/all_top_languages/")
async def all_top_languages(num_languages: int):
    folder_path = "data1"
    result = []

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".XLSX"):
            file_path = os.path.join(folder_path, file_name)
            state_name = file_name.replace("_", " ").replace(".XLSX", "")
            try:
                total_speakers_top, first_subsidiary_top, second_subsidiary_top = process_file(file_path, num_languages)
                
                # Collect data for the current state
                for i in range(num_languages):
                    row = [
                        state_name,
                        total_speakers_top.iloc[i]['Language'] if i < len(total_speakers_top) else '',
                        total_speakers_top.iloc[i]['Persons'] if i < len(total_speakers_top) else '',
                        first_subsidiary_top.iloc[i]['Language'] if i < len(first_subsidiary_top) else '',
                        first_subsidiary_top.iloc[i]['Persons'] if i < len(first_subsidiary_top) else '',
                        second_subsidiary_top.iloc[i]['Language'] if i < len(second_subsidiary_top) else '',
                        second_subsidiary_top.iloc[i]['Persons'] if i < len(second_subsidiary_top) else ''
                    ]
                    result.append(row)
            except HTTPException as e:
                continue

    # Create a DataFrame and ensure unique languages with the highest number of speakers
    result_df = pd.DataFrame(result, columns=[
        'State name', 'Top language', 'Number of speakers', 
        'Top first subsidiary language', 'Number of speakers (first subsidiary)',
        'Top second subsidiary language', 'Number of speakers (second subsidiary)'
    ])

    # Aggregation to ensure unique languages with the highest number of speakers
    result_df = result_df.groupby(['State name', 'Top language'], as_index=False).agg({
        'Number of speakers': 'max',
        'Top first subsidiary language': 'first',
        'Number of speakers (first subsidiary)': 'first',
        'Top second subsidiary language': 'first',
        'Number of speakers (second subsidiary)': 'first'
    })

    output_file_path = os.path.join(folder_path, "All_State_Bilingual_Data.xlsx")
    result_df.to_excel(output_file_path, index=False)

    return {"detail": "Summary file created", "file_path": output_file_path}



# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
