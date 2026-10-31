![Banner](banner.png)

# dso-free-text-pseudonymizer
Replaces each line of free-form text (for example, in a 'comments' field) with a pseudonym generated using a keyed hash and a seeded random number generator, so that the same input line always maps to the same pseudonym within a run that shares the same seed and the same key. Utilizes `hashlib` and `faker`. Focused on tools for sanitizing and obfuscating sensitive data within text files and structured data formats.

## What the output does and does not show
The output file holds pseudonyms, not the original text. The mapping from a line to its pseudonym is an HMAC keyed by an operator secret, so verification works like this:

- With a key supplied (`--key` or the `DSO_PSEUDONYMIZER_KEY` environment variable): the key holder can verify a guessed line against its pseudonym by recomputing the mapping with the same seed and key. Anyone without the key cannot verify a guess in that way.
- With no key supplied: the run key is derived from a fresh random value that is generated for that run and is never stored or logged. That run's mapping cannot be reproduced or checked afterwards, by anyone, and two runs over the same input with the same seed will differ.

This is obfuscation, not encryption. Treat the key like any other secret if you supply one.

## Install
`git clone https://github.com/ShadowGuard-AI/dso-free-text-pseudonymizer`

## Usage
`python main.py input.txt output.txt [--seed 42] [--locale en_US] [--key OPERATOR_SECRET] [--debug]`

The input file is read in full before the output file is opened. If the output path resolves to the input file, in any spelling (the same path, a `./` alias, or a symlink to the input), the run refuses and exits with code 1 before any file is opened, and the input is left unchanged. If pseudonym generation fails, for example with an unknown locale, the run exits with code 1 and writes no output, so the original text is never copied to the output on an error. An empty input file exits with a non-zero code, logs a plain `No text processed` line, and does not report completion.

## Parameters
- `input_file`: Path to the input text file.
- `output_file`: Path to the output file with pseudonymized text. It must not resolve to the input file.
- `--seed`: Seed for the random number generator (default: 42). The same seed and the same key reproduce a run byte for byte; a different seed produces different pseudonyms.
- `--locale`: Locale for generating fake data (default: en_US). See the faker documentation for available locales.
- `--key`: Operator secret that keys the pseudonym mapping. The `DSO_PSEUDONYMIZER_KEY` environment variable can supply it instead. If neither is given, a fresh random key is used for the run and never stored.
- `--debug`: Enable debug logging.
- `-h`: Show help message and exit.

## License
Copyright (c) ShadowStrikeHQ
