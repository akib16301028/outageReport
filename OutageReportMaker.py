# Step 3: Upload Previous Outage Data File
st.subheader("Upload Previous Outage Data")

uploaded_previous_file = st.file_uploader("Please upload a Previous Outage Excel Data file", type="xlsx")

if uploaded_previous_file:
    xl_previous = pd.ExcelFile(uploaded_previous_file)
    
    if 'Report Summary' in xl_previous.sheet_names:
        # Parse the 'Report Summary' sheet, starting from row 3 for column headers
        df_previous = xl_previous.parse('Report Summary', header=2)  # Header starts from row 3 (index 2)
        df_previous.columns = df_previous.columns.str.strip()
        
        # Check if the necessary columns exist
        if 'Elapsed Time' in df_previous.columns and 'Zone' in df_previous.columns and 'Tenant' in df_previous.columns:
            
            # Convert Elapsed Time to hours
            def convert_to_hours(elapsed_time):
                try:
                    # Handle time format using pandas Timedelta conversion
                    total_seconds = pd.to_timedelta(elapsed_time).total_seconds()
                    hours = total_seconds / 3600  # Convert seconds to hours
                    return round(hours, 2)
                except Exception as e:
                    return 0  # Handle any unexpected errors by returning 0 hours

            df_previous['Elapsed Time (hours)'] = df_previous['Elapsed Time'].apply(convert_to_hours)
            
            # Extract unique clients from the Tenant (Client) column
            clients = df_previous['Tenant'].str.strip().str.title().unique().tolist()

            # Normalize client names to match with the previously stored client info (case-insensitive match)
            selected_client = st.selectbox("Select a Client (Tenant)", clients)
            
            # Filter the data for the selected client (case-insensitive comparison)
            df_filtered = df_previous[df_previous['Tenant'].str.strip().str.title() == selected_client]

            # If filtered data exists for the selected client
            if not df_filtered.empty:
                st.write(f"Showing data for Client: {selected_client}")

                # Create Pivot Table for Zone and Elapsed Time (for the selected client)
                pivot_elapsed_time = df_filtered.pivot_table(
                    index='Zone',
                    values='Elapsed Time (hours)',
                    aggfunc='sum'
                ).reset_index()

                st.write("Pivot Table for Elapsed Time by Zone (Filtered by Client)")
                st.table(pivot_elapsed_time)

                # You can store this result for further usage in the Outage table processing step
                
            else:
                st.error(f"No data available for the client '{selected_client}'")

        else:
            st.error("The required columns 'Elapsed Time', 'Zone', and 'Tenant' are not found.")
    else:
        st.error("The 'Report Summary' sheet is not found.")
else:
    st.warning("Please upload a valid Previous Outage Excel file.")
