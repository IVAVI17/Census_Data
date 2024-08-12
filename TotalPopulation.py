import os
import pandas as pd

folder_path = 'data'

results = {}

for file_name in os.listdir(folder_path):
    if file_name.endswith('.XLSX') or file_name.endswith('.xls'):

        file_path = os.path.join(folder_path, file_name)


        df = pd.read_excel(file_path)


        df.columns = [
            "Table name", "State code", "District code", "Town code", "Area name",
            "Mother tongue code", "Mother tongue name", "Unnamed: 7", "Unnamed: 8",
            "Unnamed: 9", "Rural P", "Unnamed: 11", "Unnamed: 12",
            "Urban P", "Unnamed: 14", "Unnamed: 15"
        ]
        df.columns = df.columns.str.strip()


        df['Mother tongue code'] = df['Mother tongue code'].astype(str)

        filtered_df = df[df['Mother tongue code'].str[-3:] == '000']

        total_sum_rural = filtered_df['Rural P'].sum()
        total_sum_urban = filtered_df['Urban P'].sum()

        state_name = file_name.replace('.XLSX', '').replace('.xls', '')
        results[state_name] = {
            'Total Rural P Sum': total_sum_rural,
            'Total Urban P Sum': total_sum_urban
        }

results_df = pd.DataFrame.from_dict(results, orient='index').reset_index()
results_df.columns = ['State Name', 'Total Rural P Sum', 'Total Urban P Sum']

# Save the results DataFrame to a new Excel file
output_file_path = os.path.join(folder_path, 'total_population_sum.xlsx')
results_df.to_excel(output_file_path, index=False)

print(f"Results have been saved to {output_file_path}")
