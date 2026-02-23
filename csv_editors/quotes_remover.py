import csv
import chardet

# pip install chardet - Make sure to install chardet through pip
# Sample field = " ''"

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
        return result['encoding']

def remove_empty_fields_from_csv(input_file, output_file):
    encoding = detect_encoding(input_file)
    print(f"Detected encoding: {encoding}")

    # Read the CSV file with the detected encoding
    with open(input_file, 'r', newline='', encoding=encoding) as infile:
        reader = csv.reader(infile)
        rows = [row for row in reader]

    # Process rows to remove empty fields
    cleaned_rows = []
    for row in rows:
        cleaned_row = [value if value != " ''" else ' ' for value in row]
        cleaned_rows.append(cleaned_row)
        # Uncomment the line below to prevent all rows from printing.
        # print(cleaned_row) 

    # Write the cleaned data back to a new CSV file
    with open(output_file, 'w', newline='', encoding=encoding) as outfile:
        writer = csv.writer(outfile)
        writer.writerows(cleaned_rows)
    print("Completed removing empty fields from the CSV" + input_file + " file.")
    
# Usage
input_file = 'input.csv'
output_file = 'output.csv'
remove_empty_fields_from_csv(input_file, output_file)