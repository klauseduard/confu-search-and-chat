#!/bin/bash
#
# This script is to be used as part of a pipeline requiring the page we download.
# It was iteratively refactored and improved with the help of chatGPT
# (GPT-4 / GPT-3.5) until # approved by GPT-4
#
############

E_BADARGS=65    
E_HTTPERR=66
E_MISSINGUTILITY=67

error() {
    local message="$1"
    local exit_code="$2"
    echo "Error: $message" >&2
    usage
    exit $exit_code
}

usage() {
    cat <<USAGE
Usage:
    $(basename "$0") -P PAGE_ID -o OUTPUT_FILE

Example: $(basename "$0") -P 1111 -o file.json
USAGE
}

api_call() {
    local page_id="$1"
    curl -s \
        --user "$CONFLUENCE_USERNAME:$CONFLUENCE_PASSWORD" \
        --user-agent "$(basename "$0")/1.0" \
        --header "Accept: application/json" \
        --write-out "HTTPSTATUS:%{http_code};CONTENT_TYPE:%{content_type}" \
        --silent \
        --show-error \
        "$BASE_API_URL/$page_id?expand=body.storage" || true
}

handle_response() {
    local response="$1"
    local output_file="$2"
    local http_status=$(echo "$response" | grep -oP 'HTTPSTATUS:\K\d+')
    local content_type=$(echo "$response" | grep -oP 'CONTENT_TYPE:\K[^;]+' || echo "unknown")
    local api_result=$(echo "$response" | sed 's/;HTTPSTATUS:[0-9]*;CONTENT_TYPE:[^;]*$//')

    if [ "$http_status" -ge 400 ]; then
        if [[ "$content_type" == "application/json" ]]; then
            local error_message=$(echo "$api_result" | jq -r '.message')
            error "API request failed with HTTP status $http_status: $error_message" $E_HTTPERR
        else
            error "API request failed with HTTP status $http_status. The response content type is not JSON:\n$api_result" $E_HTTPERR
        fi
    fi

    echo "$api_result" > "$output_file"
    echo "API response saved to $output_file"
}


# Load configuration file
CONFIG_FILE="confluence.conf"
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    error "Configuration file '$CONFIG_FILE' not found." $E_BADARGS
fi


# Ensure curl and jq are installed
for utility in curl jq; do
    if ! command -v $utility >/dev/null 2>&1; then
        error "$utility utility is required but not installed." $E_MISSINGUTILITY
    fi
done

if [ $# -ne 4 ]; then
    usage
    exit $E_BADARGS
fi

while getopts ":P:o:" opt; do
    case $opt in
        P)
            PAGE_ID="$OPTARG"
            ;;
        o)
            OUTPUT_FILE="$OPTARG"
            ;;
        \?)
            error "Invalid option: -$OPTARG" $E_BADARGS
            ;;
        :)
            error "Option -$OPTARG requires an argument." $E_BADARGS
            ;;
    esac
done



# Validate input
if ! [[ "$PAGE_ID" =~ ^[1-9][0-9]*$ ]]; then
    error "Page ID must be a positive integer." $E_BADARGS
fi


# Make the API call
echo "Making the API call with curl"
RESPONSE=$(api_call "$PAGE_ID")

# Handle API response
echo "Handling API response"
handle_response "$RESPONSE" "$OUTPUT_FILE"
