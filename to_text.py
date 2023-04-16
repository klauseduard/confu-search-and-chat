import sys
import json
import argparse
from bs4 import BeautifulSoup
import html2text


class JSONDecodeError(Exception):
    pass


class FileWriteError(Exception):
    pass

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Convert Confluence JSON to plain text.')
    parser.add_argument('input_file', type=argparse.FileType('r'), metavar='INPUT_FILE', help='Path to the input JSON file.')
    parser.add_argument('output_file', type=argparse.FileType('w'), metavar='OUTPUT_FILE', help='Path to the output plain text file.')

    return parser.parse_args()


def configure_html2text() -> html2text.HTML2Text:
    """
    Configure and return an instance of html2text.HTML2Text.

    Returns:
        html2text.HTML2Text: Configured instance of html2text.HTML2Text.
    """
    text_maker = html2text.HTML2Text()
    text_maker.body_width = 0
    text_maker.ignore_links = True
    text_maker.ignore_images = True

    return text_maker


def to_text(input_file: argparse.FileType, output_file: argparse.FileType) -> None:
    """
    Convert a Confluence JSON file to plain text, preserving preformatted text.

    Args:
        input_file (argparse.FileType): Input JSON file object.
        output_file (argparse.FileType): Output plain text file object.
    """
    try:
        data = json.load(input_file)
        html_content = data['body']['storage']['value']
    except json.JSONDecodeError as e:
        raise JSONDecodeError(f"Error parsing JSON: {e}")

    soup = BeautifulSoup(html_content, 'html.parser')

    # Handle preformatted text
    for pre_tag in soup.find_all('ac:plain-text-body'):
        pre_tag.string = f"```\n{pre_tag.string}\n```"

    # Convert HTML to plain text
    text_maker = configure_html2text()
    plain_text = text_maker.handle(str(soup))

    try:
        output_file.write(plain_text)
    except IOError as e:
        raise FileWriteError(f"Error writing output file: {e}")


def main() -> None:
    """
    Execute the main function of the script: parse command-line arguments, then convert the Confluence JSON file to plain text.
    """
    args = parse_arguments()
    with args.input_file as input_file, args.output_file as output_file:
        try:
            to_text(input_file, output_file)
        except (JSONDecodeError, FileWriteError) as e:
            print(e)
            sys.exit(1)


if __name__ == "__main__":
    main()
