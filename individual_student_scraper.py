import os
import sys
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.osmania.ac.in/*ENTER YOUR RESULT URL*"

## ===========================================================================
### Functions

# Function to fetch results from a given URL
def fetch_result(hall_ticket_no, html_file_path):

    data = {
        "mbstatus": "SEARCH", 
        "htno": hall_ticket_no
    }

    try:
        # Send HTTP request with the hall ticket number
        response = requests.post(BASE_URL, data=data)
        response.raise_for_status()
    except KeyboardInterrupt:
        print("\n\nKeyboard Interrupt!!!\nExiting...\n")
        sys.exit(0)
    except requests.exceptions.RequestException as e:
        print("\n\nCheck your Internet Connection!!!\n\nAn error occurred while making a HTTP request:", e, "\n")
        sys.exit(1)

    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
    else:
        print(f"\n\nFailed to fetch result for Hall Ticket No {hall_ticket_no}. \nStatus Code: {response.status_code}\n")
        sys.exit(1)

    write_to_html(soup, html_file_path)

## --------------------------------------------------------------------------
# Function to write to HTML
def write_to_html(result_soup, html_file_path):
    try:
        with open(html_file_path, 'w', encoding='utf-8') as html_file:
            # Write the HTML content of the BeautifulSoup object to the file
            html_file.write(str(result_soup))

            # Run Prettier CLI to format the HTML file
            os.system(f"npx prettier --write {html_file_path}") #> /dev/null 2>&1")
    except PermissionError:
        print(f"\nPermission denied for writing to {html_file_path} file!\nMake sure the file isn't open.\n")
        sys.exit(1)

## --------------------------------------------------------------------------
# Function to fetch result and save as HTML
def fetch_result_and_save_as_html(hall_ticket_number):
    roll_number = int(hall_ticket_number[-2:])
    hall_ticket_no = f"{hall_ticket_number[:-2]}{roll_number:03d}"

    html_file_path = os.path.join(RESULTS_DIRECTORY, f"{hall_ticket_no}.html")

    print(f"\nFetching \"{hall_ticket_number}\" results....")

    return fetch_result(hall_ticket_number, html_file_path)

### ===========================================================================
## Main 
#
if __name__ == '__main__':
    # Create Result directory
    workingDirectory = os.getcwd()
    RESULTS_DIRECTORY = 'Student-Result'
    path = os.path.join(workingDirectory, RESULTS_DIRECTORY)

    os.makedirs(path, exist_ok=True)

    # Specify Hall Ticket details
    college_code = 0000
    year_of_join = 00
    branch_code = 000
    roll_number = 00

    result_file = fetch_result_and_save_as_html(f"{college_code}{year_of_join}{branch_code}{roll_number}")

    print(f"\nFetching Result Successful !!!\nResults File name: {result_file}\n")
