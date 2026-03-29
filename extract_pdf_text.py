#!/usr/bin/env python3
from pypdf import PdfReader

file_path = 'data/input_ft2/130600113437_202407090136.pdf'
reader = PdfReader(file_path)
text = ""
for page in reader.pages:
    text += page.extract_text() or ""
print("Extracted text:")
print(repr(text[:1000]))