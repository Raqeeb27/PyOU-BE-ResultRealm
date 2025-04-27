import os
import csv
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.osmania.ac.in/*ENTER YOUR RESULT URL*"

# Function to filter out dictionaries with 'No Change' as value for 'Name' key
def filter_no_change(records):
    filtered_records = [record for record in records if record['Name'] != 'No Change']
    return filtered_records


def get_result_and_write_to_csv(hall_ticket_prefix, results_directory):

    # Specify the file path for the CSV file
    csv_file_path = f"{results_directory}\{hall_ticket_prefix}.csv"

    # Open the CSV file for writing
    with open(csv_file_path, 'w', newline='') as csv_file:
        # Specify the CSV columns
        fieldnames = ["Hall Ticket No.", "Name", "Father's Name", "Semester", "Result with SGPA", "Theory", "Labs", "Semesters", "Passed", "Promoted", "Overall"]

        # Create a CSV writer object
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # Write the header row to the CSV file
        csv_writer.writeheader()

        result_data = []
        consecutive_not_found_count = 0  # To count consecutive "Hall Ticket Not Found" occurrences

        # Loop through all the roll numbers starting from 1
        roll_suffix = 1

        print("\nFetching results....")

        while True:

            hall_ticket_no = f"{hall_ticket_prefix}{roll_suffix:03d}"

            # Prepare the data to be sent in the POST request
            data = {
                "mbstatus": "SEARCH",
                "htno": hall_ticket_no
            }

            try:
                # Send HTTP request with the hall ticket number
                response = requests.post(BASE_URL, data=data)
            except KeyboardInterrupt:
                print("\nKeyboard Interrupt!!!\nExiting...\n")
                exit(0)
            except:
                print(f"\nCheck your Internet Connection!!!\n\nAn error occured while making a HTTP request: !!!\nExiting....\n\n")
                exit(0)

            if response.status_code == 200:
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find the <b> tags containing the names
                name_tags = soup.find_all('b')

                # Iterate through the <b> tags and extract the names
                names = [name.get_text(strip=True) for name in name_tags]

                if names[1] == f'The Hall Ticket Number "{hall_ticket_no}" Is No CHANGE.':

                    consecutive_not_found_count += 1

                    keys = ["Hall Ticket No.", "Name", "Father's Name", "Semester", "Result with SGPA", "Theory", "Labs", "Semesters", "Passed", "Promoted", "Overall"]
                    result_data.append({keys[0]: hall_ticket_no[8:], **{key: 'No Change' for key in keys[1:]}})

                    if roll_suffix == 115:
                        roll_suffix = 300
                        consecutive_not_found_count = 0
                    elif consecutive_not_found_count >= 10 and roll_suffix > 300:
                        break


                else:
                    consecutive_not_found_count = 0   # Reset the count

                    # Find the total subjects written with labs
                    marks_details_position = names.index('Marks Details')
                    result_position = names.index('Result')
                    total_subjects = int((result_position - marks_details_position -1)/4)

                    # Find the total labs written
                    count_LAB = sum(1 for element in names if "LAB" in element)

                    # Find the total semesters written
                    result_with_SGPA = names.index('Result With SGPA')
                    enter_hall_ticket_no = names.index('Enter  Hall Ticket No. :')
                    semesters_written = int((enter_hall_ticket_no - result_with_SGPA -1)/3)

                    # Find the total passed semesters
                    count_PASSED = sum(1 for element in names if "PASSED" in element)
                    count_COMPLETED = sum(1 for element in names if "COMPLETED" in element)

                    # Find the total Promoted semesters
                    count_PROMOTED = sum(1 for element in names if "PROMOTED" in element)

                    # Calculate Overall result
                    overall_status = "All Clear" if semesters_written == count_PASSED + count_COMPLETED else "Pending"


                    result_data.append({
                        "Hall Ticket No.": names[2][8:],
                        "Name": names[4],
                        "Father's Name": names[5],
                        "Semester": names[-4],
                        "Result with SGPA": names[-3],
                        "Theory": total_subjects - count_LAB,
                        "Labs": count_LAB,
                        "Semesters": semesters_written,
                        "Passed": count_PASSED + count_COMPLETED,
                        "Promoted": count_PROMOTED,
                        "Overall": overall_status,
                    })

            else:
                print(f"\nFailed to fetch result for Hall Ticket No {hall_ticket_no}. \nStatus Code: {response.status_code}\n")
                break

            roll_suffix += 1

        # Filter out dictionaries with 'No Change' as value for 'Name' key
        filtered_data = filter_no_change(result_data)

        # Remove the last 4 records from the result_data list
        #result_data = result_data[:-4]

        for result_entry in filtered_data:
            # Write only the required columns to the CSV file
            keys_to_write = ["Hall Ticket No.", "Name", "Father's Name", "Semester", "Result with SGPA", "Theory", "Labs", "Semesters", "Passed", "Promoted", "Overall"]
            csv_writer.writerow({key: result_entry[key] for key in keys_to_write})

    print(f"\nFetching Results Successfull !!!\nResults File name: {csv_file_path}\n")

### ===========================================================================
## Main
#

if __name__ == '__main__':

    # Setting up Result directory
    workingDirectory = os.getcwd()
    results_dir = 'Re-eval-Results'
    path = os.path.join(workingDirectory, results_dir)

    # Creating output directory
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except:
        print(f"\nError in Creating {results_dir} directory\n")
        exit()

    # Specify Hall Ticket details
    college_code = 0000
    year_of_join = 00
    branch_code = 000

    # Call the main function to fetch results and write to CSV
    get_result_and_write_to_csv(f"{college_code}{year_of_join}{branch_code}", results_dir)
