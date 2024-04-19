import os

def check_prettier():
    # Check if Prettier is installed globally
    if not is_installed("prettier --version"):
        install_preitter("npm install --global prettier", "globally")

    # Check if Prettier is installed locally
    if not is_installed("npx prettier --version"):
        install_preitter("npm install --save-dev prettier", "locally")

def is_installed(command):
    try:
        return os.system(f"{command}") == 0
    except:
        return False

def install_preitter(command, message):
    if input(f"Prettier is not installed {message}. Do you want to install it? (Y/N): ").upper() in ['Y', 'YES', '']:
        try:
            os.system(f"{command}")
            print(f"Successfully installed {message}!!!")
        except:
            print(f"Error in installing {message}!!\n\nExiting....\n")
            exit(1)
    else:
        print(f"Prettier not installed {message}!!\n\nExiting....\n")
        exit(0)

def format_html_files(folder_path):
    print(f"\nFormatting {folder_path} HTML files....\n")
    # Get a list of all HTML files in the folder
    html_files = [file for file in os.listdir(folder_path) if file.endswith(".html")]

    # Run Prettier CLI to format each HTML file
    for html_file in html_files:
        html_file_path = os.path.join(folder_path, html_file)
        os.system(f"npx prettier --write {html_file_path}")

# Path to the folder containing HTML files
folder_path = "PATH TO FOLDER CONTAINING HTML FILES"

# Install Prettier if necessary
check_prettier()

# Format HTML files in the folder
format_html_files(folder_path)
