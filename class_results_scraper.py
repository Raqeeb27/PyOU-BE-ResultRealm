import os
import sys
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.osmania.ac.in/*ENTER YOUR RESULT URL*"

## ===========================================================================
### Functions

def fetch_result(hall_ticket_no):
    data = {
        "mbstatus": "SEARCH", 
        "htno": hall_ticket_no
    }
    try:
        # Send HTTP request with the hall ticket number
        response = requests.post(BASE_URL, data=data)
        response.raise_for_status()
        return response
    
    except KeyboardInterrupt:
        print("\n\nKeyboard Interrupt!!!\nExiting...\n")
        sys.exit(0)
    except requests.exceptions.RequestException as e:
        print("\n\nCheck your Internet Connection!!!\n\nAn error occurred while making a HTTP request:", e, "\n")
        sys.exit(1)

def parse_result(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    names = [name.get_text(strip=True) for name in soup.find_all('b')]
    return soup, names

# Function to fetch results from a given URL
def fetch_result_and_save_as_html(hall_ticket_prefix, class_dir_path):

    consecutive_not_found_count = 0  # To count consecutive "Hall Ticket Not Found" occurrences
    roll_suffix = 1

    print(f"\nFetching \"{hall_ticket_prefix}\" results....")

    while True:
        hall_ticket_no = f"{hall_ticket_prefix}{roll_suffix:03d}"

        response = fetch_result(hall_ticket_no)

        if response.status_code == 200:
            
            soup, names = parse_result(response.text)

            if names[1] == f'The Hall Ticket Number "{hall_ticket_no}" Is Not Found.':
                consecutive_not_found_count += 1

                if consecutive_not_found_count >= 4:
                    if roll_suffix > 300:
                        break
                    else:
                        roll_suffix = 301    # Start from L.E students
                        consecutive_not_found_count = 0
                        continue
            else:
                consecutive_not_found_count = 0  # Reset the count
                
                html_file_path = os.path.join(class_dir_path, f"{hall_ticket_no}.html")
                write_to_html(soup, html_file_path)
        else:
            print(f"\n\nFailed to fetch result for Hall Ticket No {hall_ticket_no}. \nStatus Code: {response.status_code}\n")
            break

        roll_suffix += 1

## --------------------------------------------------------------------------
# Function to write to CSV
def write_to_html(result_soup, html_file_path):
    try:
        with open(html_file_path, 'w', encoding='utf-8') as html_file:
            # Write the HTML content of the BeautifulSoup object to the file
            html_file.write(str(result_soup))
            # Run Prettier CLI to format the HTML file
            # os.system(f"npx prettier --write {html_file_path}") #> /dev/null 2>&1")
    except PermissionError:
        print(f"\nPermission denied for writing to {html_file_path} file!\nMake sure the file isn't open.\n")

### ===========================================================================
## Main 
#
if __name__ == '__main__':

    # Specify Hall Ticket details
    college_code = 0000
    year_of_join = 00
    branch_code = 000

    main_results_dir = 'Class-Results'

    # Create Result directories
    main_dir_path = os.path.join(os.getcwd(), main_results_dir)
    class_dir = f"{college_code}{year_of_join}{branch_code}"
    class_dir_path = os.path.join(main_dir_path, class_dir)

    os.makedirs(main_dir_path, exist_ok=True)
    os.makedirs(class_dir_path, exist_ok=True)

    fetch_result_and_save_as_html(f"{college_code}{year_of_join}{branch_code}", class_dir_path)

    print(f"\nFetching Results Successful !!!\nResults Folder name: {class_dir_path}\n")
