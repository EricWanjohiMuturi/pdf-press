# pip install pypdf
from pypdf import PdfReader, PdfWriter

reader = PdfReader("large_file.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Apply compression to content streams (lossless)
for page in writer.pages:
    page.compress_content_streams() 

with open("compressed_pypdf.pdf", "wb") as f:
    writer.write(f)