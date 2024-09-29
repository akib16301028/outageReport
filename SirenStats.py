import pandas as pd
import streamlit as st

# Upload the first file (CSV)
csv_file = st.file_uploader("Upload the CSV file from Banglalink", type="csv")

# Upload the second file (XLSX)
xlsx_file = st.file_uploader("Upload the XLSX file from Eye Electronics", type="xlsx")

if csv_file is not None and xlsx_file is not None:
    # Read the CSV file
    df_csv = pd.read_csv(csv_file)

    # Read the XLSX file
    df_xlsx = pd.read_excel(xlsx_file)

    # Check the columns in the CSV file
    st.write("Columns in the CSV file:", df_csv.columns.tolist())
    
    # Check the columns in the XLSX file
    st.write("Columns in the XLSX file:", df_xlsx.columns.tolist())

    # Ensure the necessary columns are present
    required_csv_columns = ['Alarm Raised Date', 'Alarm Raised Time', 'Active for', 'Site', 'Alarm Slogan']
    required_xlsx_columns = ['Site Alias', 'Zone', 'Cluster']

    for col in required_csv_columns:
        if col not in df_csv.columns:
            st.error(f"Missing column in CSV: {col}")

    for col in required_xlsx_columns:
        if col not in df_xlsx.columns:
            st.error(f"Missing column in XLSX: {col}")

    # Preprocess Site and Site Alias columns for matching
    df_csv['Cleaned_Site'] = df_csv['Site'].str.replace('_X', '', regex=False).str.split(' ').str[0]
    df_xlsx['Cleaned_Site_Alias'] = df_xlsx['Site Alias'].str.replace(' (.+)', '', regex=True)  # Remove everything after space

    # Merge the dataframes on the cleaned columns
    merged_df = pd.merge(df_csv, df_xlsx[['Cleaned_Site_Alias', 'Zone', 'Cluster']], 
                         left_on='Cleaned_Site', right_on='Cleaned_Site_Alias', 
                         how='left')

    # Select relevant columns
    final_df = merged_df[['Alarm Raised Date', 'Alarm Raised Time', 'Active for', 'Site', 'Alarm Slogan', 'Zone', 'Cluster']]

    # Display the final result
    st.write("Final Merged DataFrame:")
    st.dataframe(final_df)

    # Optionally, save the result to a new CSV or Excel file
    output_file = st.file_uploader("Download the merged data as CSV", type="csv")
    if output_file is not None:
        final_df.to_csv('merged_data.csv', index=False)
        st.success("File saved successfully!")

