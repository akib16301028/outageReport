import requests
from bs4 import BeautifulSoup
import datetime
import streamlit as st

st.set_page_config(page_title="STL end Pending Tickets", page_icon="🗼")

st.title("STL end Pending Tickets")

# Define the scraping function
def scrape_page(session, page_url, all_tickets):
    # Access the page with the table using the session
    response = session.get(page_url)

    # Check if the access was successful
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the table with id "ticket_table_view"
        table = soup.find('table', {'id': 'ticket_table_view'})

        # Check if the table is found
        if table:
            # Iterate through each row in the table
            for row in table.find_all('tr', {'id': 'myDiv'}):
                # Extract data from each cell in the row
                cells = row.find_all('td')

                # Append the relevant data to the list (modify as needed)
                if cells:
                    ticket_id = cells[0].text.strip()
                    problem_name = cells[3].text.strip()

                    # Append the ticket ID to the global list
                    all_tickets.append({"Ticket ID": ticket_id, "Problem Category": problem_name})

        else:
            st.error("Table with id 'ticket_table_view' not found.")

    else:
        st.error(f"Failed to access the data page. Status code: {response.status_code}")

# Define a function to format the data and send a Telegram notification
def format_data(all_tickets):
    # Get the current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Initialize an empty message
    output_message = f"\n\nSTL end Pending Tickets: ({current_time})\n\n"

    output_message += f"<b>DCDB-01 Primary Disconnect:</b>\n\n"
    DCDB_tickets = [ticket['Ticket ID'] for ticket in all_tickets if any(keyword in ticket['Problem Category'].lower() for keyword in ['dcdb'])]
    output_message += ", ".join(DCDB_tickets) + "\n\n"

    output_message += "======================================================\n\n"


    output_message += f"<b>Smoke:</b>\n\n"
    smoke_tickets = [ticket['Ticket ID'] for ticket in all_tickets if any(keyword in ticket['Problem Category'].lower() for keyword in ['smoke'])]
    output_message += ", ".join(smoke_tickets) + "\n\n"

    output_message += "======================================================\n\n"


    output_message += f"<b>Door Open:</b>\n\n"
    door_tickets = [ticket['Ticket ID'] for ticket in all_tickets if any(keyword in ticket['Problem Category'].lower() for keyword in ['door'])]
    output_message += ", ".join(door_tickets) + "\n\n"

    output_message += "======================================================\n\n"

    output_message += "<b>Others:</b>\n\n"
    other_tickets = [ticket['Ticket ID'] for ticket in all_tickets if all(keyword not in ticket['Problem Category'].lower() for keyword in ['dcdb', 'smoke', 'door'])]
    output_message += ", ".join(other_tickets) + "\n\n"

    return output_message

# Define the main function
def main():
    # Create a session to maintain cookies
    session = requests.Session()

    # Define the login URL
    login_url = "http://172.20.17.50/phoenix/public/authenticate"

    # Prepare the login data
    login_data = {
        "username": "sadaf.mahmud",
        "password": "sadaf123",
    }

    # Perform the login POST request and store the session cookies
    response = session.post(login_url, data=login_data)

    # Check if the login was successful
    if response.status_code == 200:
        st.success("Login successful.")

        # Define the base URL to fetch the data from
        base_data_url = "http://172.20.17.50/phoenix/public/ViewTT?company=STL&ticket_id=&ticket_title=&dashboard_value=pending_task&ticket_status=not_closed&assigned_dept=&assigned_subcenter=&assigned_dept=&problem_category=&Search=Search"

        # Create a list to store all tickets
        all_tickets = []

        # Display a "Run" button
        if st.button("Run"):
            # Access the page with the table using the session
            response = session.get(base_data_url)

            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the pagination links
            pagination_links = soup.select('.pagination li a')

            # Check if pagination_links is not empty
            if pagination_links:
                # Extract the number of pages
                num_pages = max([int(link.text) for link in pagination_links if link.text.isdigit()])
            else:
                # If pagination_links is empty, set num_pages to 1
                num_pages = 1

            # Iterate through all pages
            for page_num in range(1, num_pages + 1):
                page_url = f"{base_data_url}&page={page_num}"
                st.write(f"Scraping data from page {page_num}")
                scrape_page(session, page_url, all_tickets)

            # Organize and display the accumulated data
            formatted_data = format_data(all_tickets)
            st.title("NOC End Pending Tickets")
            st.markdown(formatted_data, unsafe_allow_html=True)

        else:
            st.write("Click the 'Run' button to start the operation.")

    else:
        st.error("Login failed.")

# Run the Streamlit app
if __name__ == '__main__':
    main()

# Hide Streamlit style
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
