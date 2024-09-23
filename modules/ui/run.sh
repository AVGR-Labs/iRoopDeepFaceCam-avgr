#!/bin/bash

# Function to read files and print content
read_files() {
    local dir="$1"

    # Loop through each item in the directory
    for item in "$dir"/*; do
        if [ -d "$item" ]; then
            # If it's a directory, recursively call read_files
            read_files "$item"
        elif [ -f "$item" ]; then
            # If it's a file, print the filename and content
            echo "Filename: $item"
            echo "----------------------------------------"
            cat "$item"
            echo -e "\n"
        fi
    done
}

# Start reading from the current directory
read_files "$(pwd)"
