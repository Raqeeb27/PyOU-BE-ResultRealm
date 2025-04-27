import os
import csv
import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup


HEADER_FIELDS = ["Hall Ticket No.", "Student Name", "Father's Name", "Semester", "Result With SGPA", "Theory", "Labs", "Semesters Written", "Passed", "Promoted", "Overall"]

BASE_URL = "https://www.osmania.ac.in/*ENTER YOUR RESULT URL*"       # Specify Result URL


## ===========================================================================
### Functions

# Function to parse student results from result details
def parse_result_data(names):
    # Find the total subjects written with labs
    marks_details_position = names.index('Marks Details')
    result_position = names.index('Result')
    total_subjects_div_value = 4 if names[marks_details_position + 4].isdigit() else 3
    total_subjects = int((result_position - marks_details_position - 1) / total_subjects_div_value)

    semester, result_with_sgpa = (names[-4], names[-3]) if 'Year' in names else (names[-5], names[-4])

    # Find the total semesters written
    result_index = names.index('Result')
    enter_hall_ticket_no = names.index('Enter  Hall Ticket No. :')
    semesters_written = int((enter_hall_ticket_no - result_index - 4) / 3)

    # Find the total labs written
    count_LAB = sum(1 for element in names if "LAB" in element)

    # Find the total passed semesters
    count_PASSED = sum(1 for element in names if ("PASSED" in element) or ("PROMOTED" in element and element.count('-') == 1))
    count_COMPLETED = sum(1 for element in names if "COMPLETED" in element)

    # Find the total Promoted semesters
    count_PROMOTED = sum(1 for element in names if "PROMOTED--" in element)

    # Calculate Overall status
    overall_status = "All Clear" if semesters_written == count_PASSED + count_COMPLETED else "Pending"

    return {
        "Hall Ticket No.": names[2][8:],
        "Student Name": names[4],
        "Father's Name": names[5],
        "Semester": semester,
        "Result With SGPA": result_with_sgpa,
        "Theory": total_subjects - count_LAB,
        "Labs": count_LAB,
        "Semesters Written": semesters_written,
        "Passed": count_PASSED + count_COMPLETED,
        "Promoted": count_PROMOTED,
        "Overall": overall_status,
    }

## --------------------------------------------------------------------------
# Function to fetch results from a given URL
def fetch_result(hall_ticket_prefix):

    result_data = []
    consecutive_not_found_count = 0  # To count consecutive "Hall Ticket Not Found" occurrences

    roll_suffix = 1
    while True:
        hall_ticket_no = f"{hall_ticket_prefix}{roll_suffix:03d}"
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

            # Iterate through the <b> tags and extract the names
            names = [name.get_text(strip=True) for name in soup.find_all('b')]

            if names[1][:8] == 'The Hall':
                consecutive_not_found_count += 1

                result_data.append({HEADER_FIELDS[0]: hall_ticket_no[8:], **{key: 'Absent' for key in HEADER_FIELDS[1:]}})

                if consecutive_not_found_count >= 4:
                    if roll_suffix > 300:
                        break
                    else:
                        roll_suffix = 301    # Start from L.E students
                        consecutive_not_found_count = 0
                        result_data = result_data[:-4]
                        continue
            else:
                consecutive_not_found_count = 0  # Reset the count
                result_data.append(parse_result_data(names))
        else:
            print(f"\n\nFailed to fetch result for Hall Ticket No {hall_ticket_no}. \nStatus Code: {response.status_code}\n")
            break

        roll_suffix += 1

    # Remove the last 4 records from the result_data list
    result_data = result_data[:-4]

    return result_data

## --------------------------------------------------------------------------
# Function to check CSV file permission
def open_csv_file(csv_file_path, mode='w'):
    try:
        return open(csv_file_path, mode, newline='')
    except PermissionError:
        print("\nPermission denied for writing to CSV file!\nMake sure the file isn't open.\n")
        sys.exit(1)

## --------------------------------------------------------------------------
# Function to write to CSV
def write_to_csv(result_data, csv_file_path):
    with open_csv_file(csv_file_path, 'w') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=HEADER_FIELDS)
        csv_writer.writeheader()   # Write the header row
        csv_writer.writerows(result_data)
        csv_writer.writerow({})  # Write an empty row
        csv_writer.writerow({})  # Write an empty row

## --------------------------------------------------------------------------
# Function to download an image from a given URL
def get_results_and_write_to_csv(hall_ticket_prefix, results_directory):
    csv_file_path = os.path.join(results_directory, f"{hall_ticket_prefix}.csv")

    # Check CSV file Permission
    with open_csv_file(csv_file_path, 'w') as csv_file:
        pass

    print(f"\nFetching \"{hall_ticket_prefix}\" results....")

    result_data = fetch_result(hall_ticket_prefix)
    if len(result_data) == 0:
        print("\nInvalid Hallticket number!\n\nExiting....\n")
        sys.exit(1)
    write_to_csv(result_data, csv_file_path)
    return csv_file_path

## --------------------------------------------------------------------------
# Function to assign rankings based on SGPA
def assign_rankings(results_file, overall=False, current=False):
    df = pd.read_csv(results_file)

    if overall ^ current == False:
        print("\nInvalid Boolean Combination\nUnable to assign SGPA rankings")
    else:
        filtered_df = df[(df['Overall'] == 'All Clear') if overall else ((df['Result With SGPA'].str.startswith('PASSED')) | (df['Result With SGPA'].str.contains('PROMOTED-') & (df['Result With SGPA'].str.count('-') == 1)))]

        if not filtered_df.empty:

            RANKINGS = 'Overall-Rankings' if overall else 'Rankings'

            # Split the 'Result With SGPA' column by '-' and extract the second part
            result_sgpa_values = filtered_df['Result With SGPA'].str.split('-').str[1]

            # Convert the extracted values to float and create a list
            result_sgpa_values_list = result_sgpa_values.astype(float).tolist()

            sorted_values = sorted(set(result_sgpa_values_list), reverse=True)

            rankings_dict = {value: rank for rank, value in enumerate(sorted_values, start=1)}

            for index, row in filtered_df.iterrows():
                # Extract numeric value from 'Result With SGPA' column
                numeric_value = float(row['Result With SGPA'].split('-')[1])

                ranking = rankings_dict.get(numeric_value, None)  # Assign ranking from the dictionary

                df.loc[index, RANKINGS] = ranking  # Update the 'Rankings' column

            df.to_csv(results_file, index=False)

## --------------------------------------------------------------------------
# Function to calculate results statistics
def result_stats(results_file):
    df = pd.read_csv(results_file)

    # Count the number of rows with the specified conditions
    pass_count = ((df['Result With SGPA'].str.contains('PASSED')) |
                ((df['Result With SGPA'].str.contains('PROMOTED')) & (df['Result With SGPA'].str.count('-') == 1))).sum()
    all_clear_count = df['Overall'].value_counts().get("All Clear", 0)

    # Append "Passed" and "Overall" entries
    stats_row = {
        "Student Name": f'Passed - \'{pass_count}\'',
        "Father's Name": f'All Clear - \'{all_clear_count}\'',
    }

    stats_df = pd.DataFrame([stats_row])
    # Concatenate the new DataFrame with the original DataFrame
    df = pd.concat([df, stats_df], ignore_index=True)

    # Create an empty row any a row with the first column value as "Students Passed" title
    empty_row = pd.DataFrame([{}], columns=df.columns)
    side_heading_row = pd.DataFrame([{"Hall Ticket No.": "Students Passed:"}], columns=df.columns)

    # Concatenate the original DataFrame, empty rows, special row, and additional empty row
    df = pd.concat([df, empty_row], ignore_index=True)
    df = pd.concat([df, empty_row], ignore_index=True)
    df = pd.concat([df, side_heading_row], ignore_index=True)
    df = pd.concat([df, empty_row], ignore_index=True)

    header_row = {
        "Hall Ticket No.": "Rankings",
        "Student Name": "Hall Ticket No.",
        "Father's Name": "Student Name",
        "Semester": "Father's Name",
        "Result With SGPA": "Result With SGPA",
    }
    header_df = pd.DataFrame([header_row])
    df = pd.concat([df, header_df], ignore_index=True)
    df = pd.concat([df, empty_row], ignore_index=True)

    # Sort the DataFrame by Rankings in descending order and keep the rows where Rankings is not null
    sorted_df = df[~df['Rankings'].isna()].sort_values(by='Rankings', ascending=True)

    for students in range(len(sorted_df)):
        student_hall_ticket = sorted_df["Hall Ticket No."].values[students]
        student_name = sorted_df["Student Name"].values[students]
        student_father_name = sorted_df["Father's Name"].values[students]
        student_sgpa = sorted_df["Result With SGPA"].values[students]
        student_ranking = sorted_df["Rankings"].values[students]

        student_row = {
            "Hall Ticket No.": student_ranking,
            "Student Name": student_hall_ticket,
            "Father's Name": student_name,
            "Semester": student_father_name,
            "Result With SGPA": student_sgpa,
        }
        passed_df = pd.DataFrame([student_row])
        df = pd.concat([df, passed_df], ignore_index=True)

    df.to_csv(results_file, index=False)


### ===========================================================================
## Main
#
if __name__ == '__main__':
    # Create Result directory
    workingDirectory = os.getcwd()
    results_dir = 'Results'
    path = os.path.join(workingDirectory, results_dir)

    os.makedirs(path, exist_ok=True)

    # Specify Hall Ticket details
    college_code = 0000
    year_of_join = 00
    branch_code = 000

    results_file = get_results_and_write_to_csv(f"{college_code}{year_of_join}{branch_code}", results_dir)

    # assign rankings
    assign_rankings(results_file, current=True)
    assign_rankings(results_file, overall=True)

    # calculate the results statistcs
    result_stats(results_file)

    print(f"\nFetching Results Successful !!!\nResults File name: {results_file}\n")
