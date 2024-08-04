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
        # Read the Excel file, skipping the first three rows
        df = pd.read_excel(file_path, skiprows=3)
        
        # Rename columns to match the expected structure
        df.columns = [
            "Table name", "State code", "District code", "Town code", "Area name",
            "Mother tongue code", "Mother tongue name", "Unnamed: 7", "Unnamed: 8",
            "Unnamed: 9", "Rural P", "Unnamed: 11", "Unnamed: 12",
            "Urban P", "Unnamed: 14", "Unnamed: 15"
        ]

        # Print dataframe for debugging
        print("Dataframe after reading the file:")
        print(df.head())
        
        # Clean column names by stripping leading/trailing whitespace
        df.columns = df.columns.str.strip()
        
        # Convert 'District code' to string and filter rows where 'District code' is '0.0'
        df['District code'] = df['District code'].astype(str)
        df_filtered = df[df['District code'] == '0.0']
        
        # Print filtered dataframe for debugging
        print("Dataframe after filtering 'District code' == '0.0':")
        print(df_filtered.head())

        # Ensure the required columns are present
        if 'Mother tongue name' not in df_filtered.columns or 'Urban P' not in df_filtered.columns:
            raise HTTPException(status_code=500, detail="'Mother tongue name' or 'Urban P' column not found")

        # Clean 'Mother tongue name' column values
        df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip()

        # Print the 'Mother tongue name' column for debugging
        print("Mother tongue names and Totals before grouping:")
        print(df_filtered[['Mother tongue name', 'Urban P']])

        # Get the total speakers
        df_grouped = df_filtered[['Mother tongue name', 'Urban P']].groupby('Mother tongue name').sum().reset_index()

        # Print dataframe after grouping for debugging
        print("Dataframe after grouping by 'Mother tongue name':")
        print(df_grouped.head())

        # Sort by the total speakers in descending order
        df_sorted = df_grouped.sort_values(by='Urban P', ascending=False)

        # Get the top N most spoken languages
        top_languages = df_sorted.head(num_languages).to_dict(orient='records')

        return {"state": state_name, "top_languages": top_languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    
def get_district_code(state_name: str, district_name: str) -> str:
    census_file_path = r"./District_Codes.xlsx"
    if not os.path.exists(census_file_path):
        raise HTTPException(status_code=404, detail="Census file not found")

    census_df = pd.read_excel(census_file_path)
    
    # Print actual columns for debugging
    print("Columns in census file:", census_df.columns.tolist())

    # Clean column names by stripping leading/trailing whitespace and newlines
    census_df.columns = census_df.columns.str.replace('\n', ' ').str.strip()
    
    # Ensure column names are correctly identified
    expected_columns = ['State', 'State Code', 'District Code', 'District Name']
    if not all(col in census_df.columns for col in expected_columns):
        raise HTTPException(status_code=500, detail=f"500: Expected columns {expected_columns} not found in census file. Actual columns: {census_df.columns.tolist()}")

    # Filter the row that matches the state name and district name
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
        # Get the district code
        district_code = get_district_code(state_name, district_name)
        print(f"District code for {district_name} in {state_name} is {district_code}")

        # Read the Excel file, skipping the first three rows
        df = pd.read_excel(file_path, skiprows=3)
        
        # Rename columns to match the expected structure
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

        
        # Clean column names by stripping leading/trailing whitespace
        df.columns = df.columns.str.strip()
        
        
        # Convert 'District code' to string and filter rows where 'District code' matches
        # df['District code'] = df['District code'].astype(str)
        # df_filtered = df[df['District code'] == district_code]
        
        
        df['District code'] = pd.to_numeric(df['District code'], errors='coerce')

# Ensure the district_code is a float
        district_code = float(district_code)

# Filter the dataframe
        df_filtered = df[df['District code'] == district_code]

        
        # Print filtered dataframe for debugging
        print(f"Dataframe after filtering 'District code' == '{district_code}':")
        print(df_filtered.head())

        # Ensure the required columns are present
        if 'Mother tongue name' not in df_filtered.columns or 'Urban P' not in df_filtered.columns:
            raise HTTPException(status_code=500, detail="'Mother tongue name' or 'Urban P' column not found")

        # Clean 'Mother tongue name' column values
        df_filtered['Mother tongue name'] = df_filtered['Mother tongue name'].str.strip().str.replace(r'^\d+\s*', '', regex=True).str.strip()

        # Print the 'Mother tongue name' column for debugging
        print("Mother tongue names and Totals before grouping:")
        print(df_filtered[['Mother tongue name', 'Urban P']])

        # Get the total speakers
        df_grouped = df_filtered[['Mother tongue name', 'Urban P']].groupby('Mother tongue name').sum().reset_index()

        # Print dataframe after grouping for debugging
        print("Dataframe after grouping by 'Mother tongue name':")
        print(df_grouped.head())

        # Sort by the total speakers in descending order
        df_sorted = df_grouped.sort_values(by='Urban P', ascending=False)

        # Get the top N most spoken languages
        top_languages = df_sorted.head(num_languages).to_dict(orient='records')

        return {"state": state_name, "district": district_name, "top_languages": top_languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
