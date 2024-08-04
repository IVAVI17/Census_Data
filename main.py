from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os

app = FastAPI()

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
    num_languages = 3
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

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
