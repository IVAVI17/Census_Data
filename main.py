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
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Print column names for debugging
        print(df.columns)

        # Ensure column names are correctly identified
        if 'District code' not in df.columns:
            raise HTTPException(status_code=500, detail="'District code' column not found")

        # Filter rows where the District code is 000
        df_filtered = df[df['District code'] == 0]

        # Ensure the required columns are present
        if 'Mother tongue name' not in df_filtered.columns or 'Total' not in df_filtered.columns:
            raise HTTPException(status_code=500, detail="'Mother tongue name' or 'Total' column not found")

        # Get the total speakers (P column under the Total column)
        df_filtered = df_filtered[['Mother tongue name', 'Total']].groupby('Mother tongue name').sum().reset_index()

        # Sort by the total speakers in descending order
        df_sorted = df_filtered.sort_values(by='Total', ascending=False)

        # Get the top N most spoken languages
        top_languages = df_sorted.head(num_languages).to_dict(orient='records')

        return {"state": state_name, "top_languages": top_languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
