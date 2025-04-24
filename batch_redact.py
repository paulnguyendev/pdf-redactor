#!/usr/bin/env python
import os
import sys
import glob
from pdf_redactor import PDFRedactor

def batch_redact(input_dir, output_dir, dpi=300):
    """
    Xử lý tất cả file PDF trong thư mục input và lưu kết quả vào thư mục output
    """
    # Tạo thư mục output nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Đã tạo thư mục {output_dir}")
    
    # Lấy danh sách tất cả file PDF trong thư mục input
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"Không tìm thấy file PDF nào trong thư mục {input_dir}")
        return
    
    print(f"Tìm thấy {len(pdf_files)} file PDF trong thư mục {input_dir}")
    
    # Xử lý từng file
    for i, pdf_file in enumerate(pdf_files):
        # Lấy tên file
        filename = os.path.basename(pdf_file)
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n[{i+1}/{len(pdf_files)}] Đang xử lý: {filename}")
        
        # Khởi tạo redactor với đường dẫn đầu ra cụ thể
        redactor = PDFRedactor(pdf_file, output_path, dpi)
        result = redactor.process()
        
        if result:
            print(f"✓ Hoàn thành: {os.path.basename(result)}")
        else:
            print(f"✗ Lỗi khi xử lý: {filename}")
    
    print(f"\nHoàn thành xử lý {len(pdf_files)} file PDF")

if __name__ == "__main__":
    # Thư mục mặc định
    input_dir = "cv"
    output_dir = "cv_redact"
    dpi = 300
    
    # Cho phép chỉ định thư mục qua command line
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    if len(sys.argv) > 3:
        dpi = int(sys.argv[3])
    
    print(f"Thư mục đầu vào: {input_dir}")
    print(f"Thư mục đầu ra: {output_dir}")
    print(f"DPI: {dpi}")
    
    batch_redact(input_dir, output_dir, dpi) 