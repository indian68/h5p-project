# Documentation Translation Tool

This tool allows users to convert a codebase's documentation language (comments, README files, etc.) to a target language.

## Features

- Translates documentation in code files (comments)
- Translates markdown documentation files
- Preserves code functionality and structure
- Supports multiple target languages

## Usage

```bash
# Command line example
python translate_docs.py --target_language "German" --output_directory "./translated-docs"
```

## Parameters

- `target_language`: The language to translate the documentation into (e.g., "German", "French", "Spanish")
- `output_directory`: The directory where the translated documentation will be saved

## Requirements

- Python 3.6+
- Required Python packages (see requirements.txt)

## Installation

```bash
pip install -r requirements.txt
```