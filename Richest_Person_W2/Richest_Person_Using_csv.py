import csv

# CSV File path
file_path = 'richest_people.csv'

# Initializing variables
richest_person_name = ""
max_net_worth = -1
email_missing_count = 0
phone_missing_count = 0

try:
    # Open and read the CSV file
    with open(file_path, 'r', encoding='utf-8') as csv_file: #encoding is utf-8 to handle names of people in different languages
        csv_reader = csv.reader(csv_file)

        # Reading the first header row (Column1, Column2, ...)
        # This row is not needed for data processing
        next(csv_reader)

        # Reading the actual header row (Name, Email, ...)
        header = next(csv_reader)

        # Find the indices of the relevant columns
        try:
            name_idx = header.index('Name')
            email_idx = header.index('Email')
            phone_idx = header.index('Phone Number')
            net_worth_idx = header.index('Net Worth')
        except ValueError as e: #Error handling
            print(f"Error: Missing expected column in CSV header: {e}")
            exit()

        for row in csv_reader:
            # Adding a safety check to ensure the row has enough columns or isn't malformed
            if len(row) <= max(name_idx, email_idx, phone_idx, net_worth_idx):
                print(f"Skipping malformed row: {row}")
                continue

            name = row[name_idx]
            email = row[email_idx]
            phone_number = row[phone_idx]
            net_worth_str = row[net_worth_idx]

            # Converting net worth to a float
            # Removeing $ symbol, billion, million, and handling 'E+' scientific notation 
            cleaned_net_worth = net_worth_str.replace('$', '').replace(' billion', '').replace(' million', '').strip()
            try:
                if 'E+' in cleaned_net_worth:
                    # Handle scientific notation like 9.13273E+11 ~ happened in my older version of excel.
                    net_worth = float(cleaned_net_worth) / 1_000_000_000 # Convert to billions for consistency
                else:
                    net_worth = float(cleaned_net_worth)
            except ValueError:
                print(f"Warning: Could not parse net worth for {name}: '{net_worth_str}'. Skipping this entry for richest person calculation.")
                net_worth = -1 

            # 1. Find the richest person
            if net_worth > max_net_worth:
                max_net_worth = net_worth
                richest_person_name = name

            # 2. Count people without an email
            # Empty string or whitespace == missing email
            if not email or email.strip() == "":
                email_missing_count += 1

            # 3. Count people without phone numbers
            if not phone_number or phone_number.strip() == "":
                phone_missing_count += 1

    print("--- Analysis using csv module (reading from file) ---")
    print(f"1. The richest person in this list is: {richest_person_name} with ${max_net_worth:.0f} billion")
    print(f"2. Number of people without an email: {email_missing_count}")
    print(f"3. Number of people without phone numbers: {phone_missing_count}")

# More error handling
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found. Please ensure it's in the correct directory.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
