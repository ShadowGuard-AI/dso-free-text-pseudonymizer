#!/usr/bin/env python3

import argparse
import hashlib
import hmac
import logging
import os
import secrets
import sys
from pathlib import Path

from faker import Faker
import chardet

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(description="Pseudonymize free-form text using a keyed hash and a seeded random number generator.")
    parser.add_argument("input_file", help="Path to the input text file.")
    parser.add_argument("output_file", help="Path to the output file with pseudonymized text.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for the random number generator (default: 42).  Using the same seed will produce consistent pseudonyms.")
    parser.add_argument("--locale", type=str, default="en_US", help="Locale for generating fake data (default: en_US).  See faker documentation for available locales.")
    parser.add_argument("--key", type=str, default=None, help="Operator secret that keys the pseudonym mapping. The DSO_PSEUDONYMIZER_KEY environment variable can supply it instead. If neither is given, a fresh random key is generated for the run and never stored, so that run's mapping cannot be reproduced or checked later.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    
    return parser

def pseudonymize_text(text, seed, locale="en_US", run_key=None):
    """
    Pseudonymizes the given text using a keyed hash and Faker.

    The mapping is an HMAC of the text under the run key, combined
    with the caller supplied seed. Only a holder of the run key can
    check a guessed line against its pseudonym. A generation error
    raises instead of returning the original text.

    Args:
        text (str): The text to pseudonymize.
        seed (int): The seed for the random number generator.
        locale (str): The locale for Faker to use.
        run_key (bytes): The key for the mapping for this run.

    Returns:
        str: The pseudonymized text.
    """
    if run_key is None:
        run_key = secrets.token_bytes(32)
    message = f"{seed}\x00{text}".encode('utf-8')
    digest = hmac.new(run_key, message, hashlib.sha256).digest()
    # The 256 bit digest is cut down to a 32 bit Faker seed, because that
    # is what Faker.seed takes here. The keyed hash still decides which of
    # those seeds a line lands on, but the space of distinct pseudonym
    # sentences is the 32 bit space, not the digest space. Faker.seed is
    # also class level state: seeding it per line means this call leaves
    # the Faker generator seeded for whatever runs after it in the same
    # process.
    Faker.seed(int.from_bytes(digest, 'big') % (2**32))
    fake = Faker(locale)
    return fake.sentence()

def process_file(input_file, output_file, seed, locale, run_key=None):
    """
    Processes the input file, pseudonymizes each line, and writes the output to the output file.

    The output path is checked against the resolved input path
    before any file is opened. The input is read in full, and every
    pseudonym is generated, before the output file is opened. A
    generation error therefore writes no output at all.

    Args:
        input_file (str): The path to the input file.
        output_file (str): The path to the output file.
        seed (int): The seed for the random number generator.
        locale (str): The locale for Faker.
        run_key (bytes): The key for the mapping for this run.
    """
    if Path(input_file).resolve() == Path(output_file).resolve():
        logging.error("Output file must not be the input file; refusing to run.")
        sys.exit(1)
    if run_key is None:
        run_key = secrets.token_bytes(32)
    try:
        with open(input_file, 'rb') as f:
            raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        if encoding is None:
            encoding = 'utf-8'
            logging.warning("Could not automatically detect file encoding.  Falling back to utf-8.")
        text = raw_data.decode(encoding)
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
    except IOError as e:
        logging.error(f"IOError: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

    if text == "":
        logging.error("No text processed: the input file is empty.")
        sys.exit(1)

    # The unit of replacement is the whole line, whatever it holds: a
    # three character line and a five hundred character line each become
    # one fake sentence, so line count is the only structure the output
    # preserves. Two consequences follow. An empty line is pseudonymized
    # like any other, so a blank line in the input becomes a full sentence
    # in the output, content appearing where there was none; and a line
    # repeated anywhere in the file, or in another file under the same key
    # and seed, gets the same sentence every time.
    lines = text.splitlines()
    try:
        pseudonymized_lines = [
            pseudonymize_text(line, seed, locale, run_key) for line in lines
        ]
    except Exception as e:
        logging.error(f"Error pseudonymizing text: {e}")
        sys.exit(1)

    try:
        # Every output line is terminated, including the last, so an input
        # that ended without a newline gains one; splitlines also consumed
        # the original line endings, so CRLF input comes out LF.
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for pseudonymized_line in pseudonymized_lines:
                outfile.write(pseudonymized_line + '\n')
    except IOError as e:
        logging.error(f"IOError: {e}")
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

    supplied_key = args.key or os.environ.get("DSO_PSEUDONYMIZER_KEY")
    if supplied_key:
        run_key = supplied_key.encode('utf-8')
    else:
        # Fresh random key for this run only. It is never stored, so
        # nobody can check a guessed line against this run's
        # pseudonyms afterwards.
        run_key = secrets.token_bytes(32)
        logging.info("No key supplied: this run uses a fresh random run key that is never stored, so this run's mapping cannot be verified or reproduced afterwards.")

    process_file(args.input_file, args.output_file, args.seed, args.locale, run_key)

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
# 5. Supplying an operator key for the mapping:
#    python dso_free_text_pseudonymizer.py input.txt output.txt --key OPERATOR_SECRET
#
# Example offensive tool usage (demonstrating limitations and potential misuse):
# Suppose 'input.txt' contains sensitive data like social security numbers or credit card numbers.
# Running the pseudonymizer will replace them with fake data. However, be aware that:
# - The original data is NOT securely deleted.  It remains in the input file.
# - The pseudonymization may not be perfect.  Patterns might still be detectable in the output if the input data is highly structured.
# - This tool is NOT a substitute for proper data security measures.  It's intended for obfuscation, not secure deletion or encryption.
#
# python dso_free_text_pseudonymizer.py sensitive_data.txt obfuscated_data.txt --seed 999