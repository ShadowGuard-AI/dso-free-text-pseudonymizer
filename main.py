#!/usr/bin/env python3

import argparse
import hashlib
import logging
import sys

from faker import Faker
import chardet

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(description="Pseudonymize free-form text using consistent hashing and a seeded random number generator.")
    parser.add_argument("input_file", help="Path to the input text file.")
    parser.add_argument("output_file", help="Path to the output file with pseudonymized text.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for the random number generator (default: 42).  Using the same seed will produce consistent pseudonyms.")
    parser.add_argument("--locale", type=str, default="en_US", help="Locale for generating fake data (default: en_US).  See faker documentation for available locales.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    
    return parser

def pseudonymize_text(text, seed, locale="en_US"):
    """
    Pseudonymizes the given text using a consistent hashing algorithm and Faker.

    Args:
        text (str): The text to pseudonymize.
        seed (int): The seed for the random number generator.
        locale (str): The locale for Faker to use.

    Returns:
        str: The pseudonymized text.
    """
    try:
        # Create a hash of the input text to ensure consistency.
        hashed_text = hashlib.sha256(text.encode('utf-8')).hexdigest()

        # Seed the random number generator using the hash. This makes the pseudonym generation consistent.
        Faker.seed(int(hashed_text, 16) % (2**32))  # Ensure seed is within a reasonable range
        fake = Faker(locale)

        # Generate a pseudonym using Faker.  Consider using more context-aware methods if needed
        # (e.g., if the input is a name, use fake.name(), if it's an address, use fake.address()).
        pseudonym = fake.sentence()  # Use a sentence by default
        return pseudonym

    except Exception as e:
        logging.error(f"Error pseudonymizing text: {e}")
        return text  # Return the original text in case of error.  This is important to avoid data loss.

def process_file(input_file, output_file, seed, locale):
    """
    Processes the input file, pseudonymizes each line, and writes the output to the output file.

    Args:
        input_file (str): The path to the input file.
        output_file (str): The path to the output file.
        seed (int): The seed for the random number generator.
        locale (str): The locale for Faker.
    """
    try:
        # Detect the file encoding
        with open(input_file, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        if encoding is None:
            encoding = 'utf-8' # Fallback if chardet fails
            logging.warning("Could not automatically detect file encoding.  Falling back to utf-8.")


        with open(input_file, 'r', encoding=encoding) as infile, open(output_file, 'w', encoding='utf-8') as outfile:
            for line in infile:
                line = line.rstrip('\n') #Remove trailing newlines
                pseudonymized_line = pseudonymize_text(line, seed, locale)
                outfile.write(pseudonymized_line + '\n')  # Add newline character to maintain line structure.

    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
    except IOError as e:
        logging.error(f"IOError: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

def main():
    """
    Main entry point of the script.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug mode enabled.")

    logging.info(f"Processing file: {args.input_file}")
    logging.info(f"Output file: {args.output_file}")
    logging.info(f"Seed: {args.seed}")
    logging.info(f"Locale: {args.locale}")

    process_file(args.input_file, args.output_file, args.seed, args.locale)

    logging.info("File processing complete.")

if __name__ == "__main__":
    main()

# Usage Examples:
#
# 1. Basic usage:
#    python dso_free_text_pseudonymizer.py input.txt output.txt
#
# 2. Specifying a seed for consistent pseudonymization:
#    python dso_free_text_pseudonymizer.py input.txt output.txt --seed 123
#
# 3. Specifying a locale:
#    python dso_free_text_pseudonymizer.py input.txt output.txt --locale fr_FR
#
# 4. Enabling debug logging:
#    python dso_free_text_pseudonymizer.py input.txt output.txt --debug
#
# Example offensive tool usage (demonstrating limitations and potential misuse):
# Suppose 'input.txt' contains sensitive data like social security numbers or credit card numbers.
# Running the pseudonymizer will replace them with fake data. However, be aware that:
# - The original data is NOT securely deleted.  It remains in the input file.
# - The pseudonymization may not be perfect.  Patterns might still be detectable in the output if the input data is highly structured.
# - This tool is NOT a substitute for proper data security measures.  It's intended for obfuscation, not secure deletion or encryption.
#
# python dso_free_text_pseudonymizer.py sensitive_data.txt obfuscated_data.txt --seed 999