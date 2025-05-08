# dso-free-text-pseudonymizer
Replaces instances of free-form text (e.g., in a 'comments' field) with pseudonyms generated using a consistent hashing algorithm and a seeded random number generator, so that the same input text always maps to the same pseudonym but revealing no source information. Utilizes `hashlib` and `faker`. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

## Install
`git clone https://github.com/ShadowStrikeHQ/dso-free-text-pseudonymizer`

## Usage
`./dso-free-text-pseudonymizer [params]`

## Parameters
- `-h`: Show help message and exit
- `--seed`: No description provided
- `--locale`: No description provided
- `--debug`: Enable debug logging.

## License
Copyright (c) ShadowStrikeHQ
