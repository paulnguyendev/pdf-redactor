#!/usr/bin/env python
import os
import re
import argparse
import cv2
import numpy as np
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
from tqdm import tqdm
import time
import random
import string

# Thêm đường dẫn Poppler vào PATH
poppler_path = r"D:\Software\poppler-24.08.0\Library\bin"
if os.path.exists(poppler_path):
    os.environ["PATH"] += os.pathsep + poppler_path
    print(f"Added Poppler path: {poppler_path}")

# Thiết lập đường dẫn Tesseract
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"Added Tesseract path: {tesseract_path}")
else:
    print(f"ERROR: Tesseract không tìm thấy tại {tesseract_path}")
    print("Vui lòng cài đặt Tesseract OCR từ: https://github.com/UB-Mannheim/tesseract/wiki")
    print("Sau đó chỉnh sửa lại đường dẫn tesseract_path trong file này nếu cần")
    exit(1)

class PDFRedactor:
    def __init__(self, input_path, output_path=None, dpi=300):
        self.input_path = input_path
        self.output_path = output_path or self._get_default_output_path(input_path)
        self.dpi = dpi
        
        # Patterns for contact info
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}',
            'phone_alt': r'(?:\+?\d{1,3}[- ]?)?\d{5,12}',
            'linkedin': r'linkedin\.com/in/[\w-]+',
            'facebook': r'(?:facebook\.com|fb\.com)/[\w.]+',
            'twitter': r'(?:twitter\.com|x\.com)/[\w_]+',
            'instagram': r'instagram\.com/[\w_.]+',
            'tiktok': r'tiktok\.com/@[\w.]+',
            'github': r'github\.com/[\w-]+',
            'youtube': r'youtube\.com/(?:c/|channel/|@)?[\w-]+',
            'website': r'https?://(?:www\.)?[\w.-]+\.\w+(?:/\S*)?',
            'address': r'\d+\s+[\w\s.,]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|court|ct|plaza|square|lane|ln|parkway|pkwy)\b',
            'zalo': r'zalo\.me/\d+',
            'whatsapp': r'wa\.me/\d+',
            'skype': r'skype:[\w.]+',
            'telegram': r't\.me/[\w_]+',
            'social_handle': r'@[\w._]{3,30}\b',  # Nhận diện đa số các @ handle
        }

        # Mẫu nhận diện số điện thoại Việt Nam
        self.vn_phone_patterns = [
            r'\b0[35789]\d{8}\b',  # 10 số: 03x, 05x, 07x, 08x, 09x
            r'\b\+?84[35789]\d{8}\b',  # +84
            r'\b(?:\+?84|0)(?:3|5|7|8|9)\d{8}\b',  # Kết hợp
            r'\b(?:\+?84|0)(?:1\d{9})\b',  # Số 11 số cũ
        ]
        
        # Thêm các mẫu số điện thoại VN vào patterns
        for i, pattern in enumerate(self.vn_phone_patterns):
            self.patterns[f'vn_phone_{i}'] = pattern
    
    def _get_default_output_path(self, input_path):
        """Generate default output path by adding '_redacted' suffix"""
        base, ext = os.path.splitext(input_path)
        return f"{base}_redacted{ext}"
    
    def _get_safe_output_path(self, path):
        """Generate a safe output path if file is in use"""
        if not os.path.exists(path):
            return path
            
        # Thử mở file để kiểm tra quyền truy cập
        try:
            with open(path, "a"):
                pass
            return path
        except (IOError, PermissionError):
            # Nếu file đang bị sử dụng, tạo tên file mới
            base, ext = os.path.splitext(path)
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            new_path = f"{base}_{random_suffix}{ext}"
            print(f"File {path} đang bị sử dụng, lưu vào: {new_path}")
            return new_path
    
    def process(self):
        """Main method to process and redact the PDF"""
        # Convert PDF to images
        print(f"Converting PDF to images (DPI: {self.dpi})...")
        try:
            images = convert_from_path(self.input_path, dpi=self.dpi, poppler_path=poppler_path)
        except Exception as e:
            print(f"Error converting PDF: {e}")
            print("Make sure Poppler is installed correctly at:", poppler_path)
            return None
        
        # Process each page
        redacted_images = []
        for i, img in enumerate(tqdm(images, desc="Redacting pages")):
            # Convert PIL image to OpenCV format
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Find and redact contact information
            redacted = self._redact_contact_info(img_cv, i+1)
            
            # Convert back to PIL for saving
            redacted_pil = Image.fromarray(cv2.cvtColor(redacted, cv2.COLOR_BGR2RGB))
            redacted_images.append(redacted_pil)
        
        # Kiểm tra và tạo đường dẫn an toàn
        safe_output_path = self._get_safe_output_path(self.output_path)
        
        # Save redacted images as PDF
        print(f"Saving redacted PDF to {safe_output_path}...")
        try:
            redacted_images[0].save(
                safe_output_path, 
                save_all=True, 
                append_images=redacted_images[1:],
                resolution=self.dpi
            )
            print("Done!")
            return safe_output_path
        except Exception as e:
            print(f"Error saving PDF: {e}")
            if "Permission denied" in str(e):
                print("File đang được sử dụng. Vui lòng đóng trình đọc PDF và thử lại.")
                # Thử lưu với tên file khác
                alt_output = f"{os.path.splitext(safe_output_path)[0]}_alt_{int(time.time())}.pdf"
                print(f"Đang thử lưu với tên file khác: {alt_output}")
                try:
                    redacted_images[0].save(
                        alt_output, 
                        save_all=True, 
                        append_images=redacted_images[1:],
                        resolution=self.dpi
                    )
                    print(f"Đã lưu thành công vào: {alt_output}")
                    return alt_output
                except Exception as e2:
                    print(f"Vẫn không thể lưu file: {e2}")
            return None
    
    def _redact_contact_info(self, img, page_num):
        """Find and redact contact information in an image"""
        # Get image dimensions
        height, width, _ = img.shape
        
        # Extract text using OCR
        text = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        # Get coordinates for text boxes
        redacted = img.copy()
        
        for i in range(len(text['text'])):
            word = text['text'][i]
            if not word.strip():
                continue
                
            # Check each pattern against the word and surrounding context
            for pattern_name, pattern in self.patterns.items():
                if re.search(pattern, word, re.IGNORECASE):
                    # Extract coordinates
                    x, y = text['left'][i], text['top'][i]
                    w, h = text['width'][i], text['height'][i]
                    
                    # Add a bit of padding
                    x = max(0, x - 5)
                    y = max(0, y - 5)
                    w = min(width - x, w + 10)
                    h = min(height - y, h + 10)
                    
                    # Draw black rectangle over the text
                    cv2.rectangle(redacted, (x, y), (x + w, y + h), (0, 0, 0), -1)
                    print(f"Redacted {pattern_name} on page {page_num}: '{word}'")
        
        return redacted

def main():
    parser = argparse.ArgumentParser(description='Redact contact information from PDF CVs')
    parser.add_argument('input_pdf', help='Path to the input PDF file')
    parser.add_argument('-o', '--output', help='Path to the output PDF file')
    parser.add_argument('-d', '--dpi', type=int, default=300, help='DPI for PDF processing (higher is better but slower)')
    parser.add_argument('-p', '--poppler', help='Path to Poppler bin directory', default=poppler_path)
    
    args = parser.parse_args()
    
    if args.poppler and args.poppler != poppler_path:
        os.environ["PATH"] += os.pathsep + args.poppler
        print(f"Using Poppler path: {args.poppler}")
    
    redactor = PDFRedactor(args.input_pdf, args.output, args.dpi)
    output_path = redactor.process()
    
    if output_path:
        print(f"PDF successfully redacted and saved to: {output_path}")

if __name__ == "__main__":
    main() 