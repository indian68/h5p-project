#!/usr/bin/env python3
"""
Documentation Translation Tool

This script translates documentation (comments and markdown files) in a codebase 
to a specified target language while preserving code functionality.
"""

import os
import sys
import argparse
import re
import logging
from pathlib import Path
from typing import List, Dict, Set
import shutil
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    from googletrans import Translator
    translator = Translator()
except ImportError:
    logger.error("Required package 'googletrans' not found. Please install: pip install googletrans==4.0.0-rc1")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error initializing translator: {str(e)}")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Translate code documentation to a target language.')
    parser.add_argument('--target_language', required=True, help='The target language for translation (e.g., "German")')
    parser.add_argument('--output_directory', required=True, help='Directory to save translated files')
    parser.add_argument('--source_directory', default='.', help='Source code directory (default: current directory)')
    
    try:
        args = parser.parse_args()
        logger.info(f"Arguments parsed successfully: target_language={args.target_language}, "
                   f"output_directory={args.output_directory}, source_directory={args.source_directory}")
        return args
    except Exception as e:
        logger.error(f"Error parsing arguments: {str(e)}")
        sys.exit(1)

def is_documentation_file(file_path: str) -> bool:
    """Determine if a file is primarily documentation."""
    try:
        doc_extensions = {'.md', '.txt', '.rst', '.adoc'}
        return Path(file_path).suffix.lower() in doc_extensions
    except Exception as e:
        logger.error(f"Error checking documentation file: {str(e)}")
        return False

def is_code_file(file_path: str) -> bool:
    """Determine if a file contains code that may have comments."""
    try:
        code_extensions = {'.py', '.js', '.java', '.c', '.cpp', '.h', '.cs', '.php', '.rb', '.go', '.ts', '.swift'}
        return Path(file_path).suffix.lower() in code_extensions
    except Exception as e:
        logger.error(f"Error checking code file: {str(e)}")
        return False

def should_process_file(file_path: str) -> bool:
    """Determine if a file should be processed for translation."""
    try:
        # Skip hidden files and directories
        if Path(file_path).name.startswith('.'):
            return False
        
        # Skip binary files and certain extensions
        skip_extensions = {'.pyc', '.class', '.o', '.so', '.dll', '.exe', '.jpg', '.png', '.gif'}
        if Path(file_path).suffix.lower() in skip_extensions:
            return False
        
        return is_documentation_file(file_path) or is_code_file(file_path)
    except Exception as e:
        logger.error(f"Error checking if file should be processed: {str(e)}")
        return False

def extract_comments_from_code(content: str, file_extension: str) -> Dict[str, str]:
    """Extract comments from code files based on file type."""
    comments = {}
    try:
        if file_extension in ['.py']:
            # Python docstrings (multiline)
            docstring_pattern = r'(""".*?""")|(\'\'\'.+?\'\'\')'
            docstring_matches = re.finditer(docstring_pattern, content, re.DOTALL)
            for i, match in enumerate(docstring_matches):
                if match.group():
                    comments[f'docstring_{i}'] = match.group()
            
            # Python single line comments
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '#' in line:
                    comment_part = line.split('#', 1)[1]
                    if comment_part.strip():
                        comments[f'line_{i}'] = f'#{comment_part}'
        
        elif file_extension in ['.js', '.java', '.c', '.cpp', '.h', '.cs', '.php', '.go', '.ts', '.swift']:
            # Block comments
            block_pattern = r'/\*[\s\S]*?\*/'
            block_matches = re.finditer(block_pattern, content)
            for i, match in enumerate(block_matches):
                comments[f'block_{i}'] = match.group()
            
            # Single line comments
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '//' in line:
                    comment_part = line.split('//', 1)[1]
                    if comment_part.strip():
                        comments[f'line_{i}'] = f'//{comment_part}'
        
        logger.debug(f"Extracted {len(comments)} comments from file with extension {file_extension}")
        return comments
    except Exception as e:
        logger.error(f"Error extracting comments: {str(e)}")
        return {}

def translate_text(text: str, target_language: str) -> str:
    """Translate text to target language."""
    try:
        # Filter out empty strings
        if not text.strip():
            return text
        
        translated = translator.translate(text, dest=target_language.lower())
        return translated.text
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        logger.debug(f"Failed to translate text: {text[:100]}...")
        return text  # Return original if translation fails

def translate_comments(comments: Dict[str, str], target_language: str) -> Dict[str, str]:
    """Translate all extracted comments."""
    translated_comments = {}
    
    for key, comment in comments.items():
        try:
            translated_comment = translate_text(comment, target_language)
            translated_comments[key] = translated_comment
        except Exception as e:
            logger.error(f"Error translating comment {key}: {str(e)}")
            translated_comments[key] = comment
    
    return translated_comments

def replace_comments_in_code(content: str, original_comments: Dict[str, str], 
                           translated_comments: Dict[str, str]) -> str:
    """Replace original comments with translated ones."""
    try:
        updated_content = content
        
        # Sort keys by their position in reverse order to avoid offset issues
        keys = sorted(original_comments.keys(), key=lambda k: k.split('_')[1], reverse=True)
        
        for key in keys:
            original = original_comments[key]
            translated = translated_comments[key]
            updated_content = updated_content.replace(original, translated)
        
        return updated_content
    except Exception as e:
        logger.error(f"Error replacing comments: {str(e)}")
        return content

def process_documentation_file(file_path: str, target_language: str) -> str:
    """Process a documentation file (like markdown)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Translate the entire content for documentation files
        translated_content = translate_text(content, target_language)
        return translated_content
    except Exception as e:
        logger.error(f"Error processing documentation file {file_path}: {str(e)}")
        return ""

def process_code_file(file_path: str, target_language: str) -> str:
    """Process a code file, translating only the comments."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_extension = Path(file_path).suffix.lower()
        comments = extract_comments_from_code(content, file_extension)
        
        if not comments:
            logger.info(f"No comments found in {file_path}")
            return content
        
        translated_comments = translate_comments(comments, target_language)
        updated_content = replace_comments_in_code(content, comments, translated_comments)
        
        return updated_content
    except Exception as e:
        logger.error(f"Error processing code file {file_path}: {str(e)}")
        return ""

def process_file(file_path: str, target_language: str) -> str:
    """Process a file for translation based on its type."""
    try:
        if is_documentation_file(file_path):
            return process_documentation_file(file_path, target_language)
        elif is_code_file(file_path):
            return process_code_file(file_path, target_language)
        else:
            # For other files, just return the original content
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return ""

def find_files_to_process(source_dir: str) -> List[str]:
    """Find all files that should be processed for translation."""
    try:
        files_to_process = []
        
        for root, dirs, files in os.walk(source_dir):
            # Skip hidden directories and specific directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '.git']]
            
            for file in files:
                file_path = os.path.join(root, file)
                if should_process_file(file_path):
                    files_to_process.append(file_path)
        
        logger.info(f"Found {len(files_to_process)} files to process")
        return files_to_process
    except Exception as e:
        logger.error(f"Error finding files to process: {str(e)}")
        return []

def main():
    """Main entry point for the script."""
    try:
        args = parse_arguments()
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_directory, exist_ok=True)
        
        # Find files to process
        files_to_process = find_files_to_process(args.source_directory)
        
        if not files_to_process:
            logger.warning("No files found to process")
            return
        
        # Process each file
        for file_path in files_to_process:
            try:
                # Get relative path for creating in output directory
                rel_path = os.path.relpath(file_path, args.source_directory)
                output_file_path = os.path.join(args.output_directory, rel_path)
                
                # Create directories if they don't exist
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                
                # Process the file
                logger.info(f"Processing: {rel_path}")
                translated_content = process_file(file_path, args.target_language)
                
                if not translated_content:
                    logger.error(f"Failed to get translated content for {file_path}")
                    continue
                
                # Write the translated content to the output file
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(translated_content)
                
                logger.info(f"Successfully translated {rel_path}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                logger.debug(traceback.format_exc())
        
        logger.info(f"Translation complete. Translated files saved to {args.output_directory}")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()