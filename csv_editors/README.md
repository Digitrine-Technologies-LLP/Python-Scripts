# CSV Empty Field Remover

A lightweight Python utility that scans a CSV file for placeholder empty fields (` ''`) and replaces them with a blank space, writing the cleaned data to a new output file.

## Requirements

- Python 3.x
- [`chardet`](https://pypi.org/project/chardet/) library for automatic encoding detection

Install the dependency with:

```bash
pip install chardet
```

## Usage

1. Place your input CSV file in the same directory as the script (or provide the full path).
2. Update the `input_file` and `output_file` variables at the bottom of the script:

```python
input_file = 'input.csv'
output_file = 'output.csv'
```

3. Run the script:

```bash
python script.py
```

The cleaned CSV will be written to the specified output file.

## How It Works

| Step | Description |
|------|-------------|
| **Encoding Detection** | Uses `chardet` to automatically detect the input file's character encoding, ensuring compatibility with a wide range of CSV files. |
| **Read** | Reads the CSV using Python's built-in `csv` module with the detected encoding. |
| **Clean** | Iterates over every field in every row and replaces any field matching ` ''` with a single space. |
| **Write** | Writes the cleaned rows to the output file using the same detected encoding. |

## Configuration

**Changing the target placeholder value**

The script targets the specific placeholder ` ''` by default. To change this, update the `Sample field` variable and the list comprehension inside `remove_empty_fields_from_csv`:

```python
# Default
cleaned_row = [value if value != " ''" else ' ' for value in row]

# Example: target fields containing only whitespace
cleaned_row = [value if value.strip() != '' else ' ' for value in row]
```

**Logging processed rows**

To print each cleaned row to the console, uncomment the following line inside the loop:

```python
# print(cleaned_row)
```

## Example

**Input CSV:**
```
name,age,city
Alice,30,New York
Bob, '',''
Charlie, '',Los Angeles
```

**Output CSV:**
```
name,age,city
Alice,30,New York
Bob, , 
Charlie, ,Los Angeles
```

## Notes

- The original input file is never modified. All changes are written to the output file.
- The script preserves the original file encoding in the output file.
- If `chardet` cannot confidently detect the encoding, consider manually specifying it in the `open()` calls (e.g., `encoding='utf-8'`).