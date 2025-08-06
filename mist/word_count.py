#!/usr/bin/env python3
"""
Word Count Script for Markdown Files
Counts words in all .md files in the ../src directory and its subdirectories.
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def count_words_in_file(file_path):
    """Count words in a single markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Remove markdown syntax and count words
        # Remove headers, links, images, code blocks, etc.
        content = re.sub(r'#+\s*', '', content)  # Remove headers
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)  # Remove images
        content = re.sub(r'\[.*?\]\(.*?\)', '', content)  # Remove links
        content = re.sub(r'`.*?`', '', content)  # Remove inline code
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Remove code blocks
        content = re.sub(r'\*\*.*?\*\*', '', content)  # Remove bold
        content = re.sub(r'\*.*?\*', '', content)  # Remove italic
        content = re.sub(r'~~.*?~~', '', content)  # Remove strikethrough
        
        # Split into words and filter out empty strings
        words = re.findall(r'\b\w+\b', content)
        return len(words)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def find_markdown_files(root_dir):
    """Find all markdown files in the directory tree."""
    markdown_files = []
    root_path = Path(root_dir)
    
    for file_path in root_path.rglob('*.md'):
        markdown_files.append(file_path)
    
    return markdown_files

def main():
    """Main function to count words in all markdown files."""
    # Get the src directory path (../src from current location)
    current_dir = Path.cwd()
    src_dir = current_dir.parent / 'src'
    
    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return
    
    print(f"🔍 Searching for markdown files in: {src_dir}")
    markdown_files = find_markdown_files(src_dir)
    
    if not markdown_files:
        print("❌ No markdown files found in src directory!")
        return
    
    print(f"📁 Found {len(markdown_files)} markdown files")
    print("\n" + "="*60)
    
    # Count words in each file
    total_words = 0
    file_stats = []
    
    for file_path in sorted(markdown_files):
        word_count = count_words_in_file(file_path)
        relative_path = file_path.relative_to(src_dir)
        
        file_stats.append({
            'path': relative_path,
            'words': word_count
        })
        
        total_words += word_count
        
        # Print individual file stats
        print(f"{relative_path}: {word_count:,} words")
    
    print("\n" + "="*60)
    print(f"📊 SUMMARY")
    print(f"Total files: {len(markdown_files)}")
    print(f"Total words: {total_words:,}")
    
    # Group by directory
    dir_stats = defaultdict(int)
    for stat in file_stats:
        dir_path = stat['path'].parent
        dir_stats[str(dir_path)] += stat['words']
    
    print(f"\n📂 Words by directory:")
    for dir_path, word_count in sorted(dir_stats.items()):
        if dir_path == '.':
            print(f"src/: {word_count:,} words")
        else:
            print(f"src/{dir_path}: {word_count:,} words")
    
    # Find the file with most words
    if file_stats:
        max_file = max(file_stats, key=lambda x: x['words'])
        print(f"\n🏆 File with most words: {max_file['path']} ({max_file['words']:,} words)")
        
        # Find the directory with most words
        max_dir = max(dir_stats.items(), key=lambda x: x[1])
        print(f"📁 Directory with most words: src/{max_dir[0]} ({max_dir[1]:,} words)")

if __name__ == "__main__":
    main() 