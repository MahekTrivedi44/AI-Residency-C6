import pandas as pd #Importing pandas

# file path
file_path = 'richest_people.csv'

try: # try to
    # read the CSV file into a pandas df and skip the first row which is column 1...
    df = pd.read_csv(file_path, skiprows=[0])

    # 1. Who is the richest in this list?
    # Removeing $ symbol, billion, million, and handling 'E+' scientific notation 
    def clean_net_worth(net_worth_str):
        if isinstance(net_worth_str, str):
            cleaned = net_worth_str.replace('$', '').replace(' billion', '').replace(' million', '').strip()
            try:
                # Check for scientific notation (e.g., 9.13273E+11)
                if 'E+' in cleaned or 'e+' in cleaned:
                    return float(cleaned) / 1_000_000_000 # Convert to billions for consistency
                else:
                    return float(cleaned)
            except ValueError:
                return None # Return None for unparseable values
        return None # Handle non-string types or NaN if they appear

    df['Cleaned Net Worth'] = df['Net Worth'].apply(clean_net_worth)

    # idxmax gives index of the first occurrence of the maximum value
    richest_person = df.loc[df['Cleaned Net Worth'].idxmax()]

    richest_person_name = richest_person['Name'] #use index to find the richest person's name
    richest_person_net_worth = richest_person['Cleaned Net Worth']

    # 2. How many people are without an email?
    # null values and empty strings
    email_missing_count = df['Email'].isnull().sum() + (df['Email'] == '').sum()

    # 3. How many people are without phone numbers?
    phone_missing_count = df['Phone Number'].isnull().sum() + (df['Phone Number'] == '').sum()

    print("--- Analysis using pandas (reading from file) ---")
    print(f"1. The richest person in this list is: {richest_person_name} with ${richest_person_net_worth:.0f} billion")
    print(f"2. Number of people without an email: {email_missing_count}")
    print(f"3. Number of people without phone numbers: {phone_missing_count}")

# Error handling
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found. Please ensure it's in the correct directory.")
except KeyError as e:
    print(f"Error: Missing expected column in CSV file: {e}. Please check the column names.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
