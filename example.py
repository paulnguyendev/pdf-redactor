#!/usr/bin/env python
"""
Example script showing how to use the PDF redactor
"""
from pdf_redactor import PDFRedactor

def main():
    # Example usage of the PDFRedactor class
    input_file = "path/to/your/cv.pdf"
    
    # Basic usage with default output path and DPI
    redactor = PDFRedactor(input_file)
    output_path = redactor.process()
    print(f"Redacted PDF saved to: {output_path}")
    
    # Advanced usage with custom output path and higher DPI
    # redactor = PDFRedactor(
    #     input_path="path/to/your/cv.pdf",
    #     output_path="path/to/your/redacted_cv.pdf",
    #     dpi=400
    # )
    # output_path = redactor.process()
    # print(f"Redacted PDF saved to: {output_path}")

if __name__ == "__main__":
    main() 