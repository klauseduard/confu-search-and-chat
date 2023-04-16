import sys
import json
from bs4 import BeautifulSoup
import html2text

def main(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
        html_content = data['body']['storage']['value']

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

    with open(output_file, 'w') as f:
        f.write(plain_text)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} input_file output_file")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
