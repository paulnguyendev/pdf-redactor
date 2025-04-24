# PDF CV Redactor

Tool to automatically redact contact information from PDF CVs.

## Features

- Redacts emails, phone numbers, addresses, LinkedIn profiles, and websites
- Preserves original PDF layout
- Simple command-line interface

## Requirements

- Python 3.7+
- Tesseract OCR engine
- Poppler (required by pdf2image)

## Installation

1. Install Tesseract OCR:
   - Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - MacOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`

2. Install Poppler:
   - Windows: Download binaries from https://github.com/oschwartz10612/poppler-windows/releases/
   - MacOS: `brew install poppler`
   - Linux: `sudo apt install poppler-utils`

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Basic usage:
```
python pdf_redactor.py input.pdf
```

Specify output file:
```
python pdf_redactor.py input.pdf -o output.pdf
```

Adjust DPI for better OCR (default is 300):
```
python pdf_redactor.py input.pdf -d 400
```

## How It Works

1. Converts PDF to images
2. Uses OCR to detect text and its position
3. Applies regex patterns to identify contact information
4. Draws black rectangles over detected contact info
5. Combines redacted images back into a PDF 