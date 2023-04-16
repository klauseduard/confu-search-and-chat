#!/bin/bash
#
# The initial pipeline for generating embeddings for a single page and storing those in Redis
#
# The outline will change, as we went to store some metadata along with the embeddings.
#
# Also, we will probably try pickle format for storing the embeddings.
#


# -e: exit immediately id any command in scripy returns non-zero exit code
# -E: enables error tracing, causes functions and subshells to inherit the trap
#    setting from the parent shell
# -u: treat undefined variables as an error and exit immediately
# -o pipefail: ensure a pipeline fails if any command of the pipeline fails
set -eEuo pipefail

E_BADARGS=65
E_MISSING_UTILITY=67

# Function for cleaning up temporary files and directories
cleanup() {
    if [ -d "$output_dir" ]; then
        rm -rf "$output_dir"
        echo "Directory removed: $output_dir"
    fi
}

# Error handling
handle_error() {
    local exit_code=$?
    echo "Error: command exited with status $exit_code." >&2
    cleanup
    exit "$exit_code"
}
trap handle_error ERR

# Check if required scripts and utilities are available
for script in get_confluence_page.sh update_request.sh get_embeddings.sh store_in_redis.sh; do
    if ! command -v ./"$script" >/dev/null 2>&1; then
        echo "Error: Script $script is required but not found in the current directory." >&2
        exit $E_MISSINGUTILITY
    fi
done

# Check if python3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 interpreter is required but not installed." >&2
    exit $E_MISSINGUTILITY
fi


if [ $# -ne 1 ]
then
cat <<USAGE

Usage:
    $(basename "$0") PAGE_ID

Example: $(basename "$0") 1111

USAGE
    exit $E_BADARGS
fi

PAGE_ID="$1"
output_dir="tmp"

if [ ! -d "$output_dir" ]; then
    mkdir "$output_dir"
    echo "Directory created: $output_dir"
else
    echo "Directory already exists: $output_dir"
fi


# Download a confluence page and save it to output folder
./get_confluence_page.sh -P "$PAGE_ID" -o "$output_dir/confluence_page.json"

# Convert the data stored as json to plain text
python3 to_text.py "$output_dir/confluence_page.json" "$output_dir/confluence_page_plaintext.txt"

# Preprocess the text to better suit the needs of Embeddings API
python3 preprocess.py "$output_dir/confluence_page_plaintext.txt" "$output_dir/preprocessed.txt"

./update_request.sh "$output_dir/preprocessed.txt"
./get_embeddings.sh > embeddings.json
./store_in_redis.sh "$PAGE_ID"

# Clean up temporary files and directories
cleanup
