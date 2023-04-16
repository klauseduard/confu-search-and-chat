import sys
import json
import argparse
from bs4 import BeautifulSoup
import html2text


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Convert Confluence JSON to plain text.')
    parser.add_argument('input_file', type=str, help='Path to the input JSON file.')
    parser.add_argument('output_file', type=str, help='Path to the output plain text file.')

    return parser.parse_args()


def to_text(input_file:str, output_file:str) -> None:
    """
    Convert a Confluence JSON file to plain text, preserving preformatted text.

    Args:
        input_file (str): Path to the input JSON file.
        output_file (str): Path to the output plain text file.
    """
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
            html_content = data['body']['storage']['value']
    except (FileNotFoundError, IOError) as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    soup = BeautifulSoup(html_content, 'html.parser')

    # Handle preformatted text
    for pre_tag in soup.find_all('ac:plain-text-body'):
        pre_tag.string = f"```\n{pre_tag.string}\n```"

    # Convert HTML to plain text
    text_maker = html2text.HTML2Text()
    text_maker.body_width = 0
    text_maker.ignore_links = True
    text_maker.ignore_images = True
    plain_text = text_maker.handle(str(soup))

    try:
        with open(output_file, 'w') as f:
            f.write(plain_text)
    except (FileNotFoundError, IOError) as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

def main() -> None:
    args = parse_arguments()
    to_text(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
