import fitz
import sys

pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'input/file04.pdf'
doc = fitz.open(pdf_path)
page = doc[0]
blocks = page.get_text('dict')['blocks']

print(f"=== Analyzing {pdf_path} ===")
for block in blocks:
    if 'lines' in block:
        for line in block['lines']:
            for span in line['spans']:
                text = span['text'].strip()
                if text:
                    print(f'Size: {span["size"]:.1f}, Flags: {span["flags"]}, Font: {span["font"]}, Text: "{text}"')
