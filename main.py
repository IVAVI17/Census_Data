from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os

app = FastAPI()

class RequestModel(BaseModel):
    state_name: str
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

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
