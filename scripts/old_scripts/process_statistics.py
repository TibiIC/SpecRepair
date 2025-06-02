import argparse
import os

from spec_repair.builders.csvbuilder import CSVBuilder

description = """
TODO: fill up a description for this statistics processor
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input', type=str, help='Path to the input file to process. This should be a .txt')
    parser.add_argument('-o', '--output', type=str, help='Path to the expected output .csv file.')
    args = parser.parse_args()

    current_directory = os.getcwd()
    input_file_path = os.path.join(current_directory, args.input)
    output_file_path = os.path.join(current_directory, args.output)

    csvbuilder = CSVBuilder()

    with open(input_file_path, 'r') as input_file:
        for line in input_file:
            csvbuilder.record(line)

    # Save the DataFrame to a CSV file
    csvbuilder.save_to_file(output_file_path)

    print(f"Processed data saved to {output_file_path}")
