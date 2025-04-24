#!/usr/bin/env python
import os
import uuid
import tempfile
from flask import Flask, request, jsonify, send_file, send_from_directory, url_for
from pdf_redactor import PDFRedactor
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')

# Thư mục lưu trữ files tạm thời
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)

# Cấu hình Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

@app.route('/')
def index():
    """Trang chủ - trả về file HTML"""
    return send_from_directory('static', 'index.html')

@app.route('/health', methods=['GET'])
def health():
    """Endpoint kiểm tra API còn hoạt động không"""
    return jsonify({'status': 'ok', 'message': 'API đang hoạt động'})

@app.route('/redact', methods=['POST'])
def redact_pdf():
    """
    API endpoint để redact PDF
    
    Form data:
    - file: File PDF cần redact
    - dpi: (tùy chọn) DPI cho việc xử lý, mặc định là 300
    
    Trả về URL để tải file PDF đã redact
    """
    # Kiểm tra xem request có file không
    if 'file' not in request.files:
        return jsonify({'error': 'Không tìm thấy file trong request'}), 400
        
    file = request.files['file']
    
    # Kiểm tra tên file
    if file.filename == '':
        return jsonify({'error': 'Không có file nào được chọn'}), 400
        
    # Kiểm tra đuôi file
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Chỉ chấp nhận file PDF'}), 400
    
    # Lấy DPI từ form data, mặc định là 300
    dpi = int(request.form.get('dpi', 300))
    
    # Tạo tên file độc nhất để tránh xung đột
    unique_id = str(uuid.uuid4())
    original_filename = secure_filename(file.filename)
    base_filename, _ = os.path.splitext(original_filename)
    
    # Lưu file upload
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{original_filename}")
    file.save(upload_path)
    
    # Đường dẫn file đầu ra
    output_filename = f"{base_filename}_redacted_{unique_id}.pdf"
    output_path = os.path.join(app.config['RESULT_FOLDER'], output_filename)
    
    try:
        # Thực hiện redact PDF
        redactor = PDFRedactor(upload_path, output_path, dpi)
        result_path = redactor.process()
        
        if not result_path:
            return jsonify({'error': 'Lỗi khi xử lý file PDF'}), 500
        
        # Tạo file_id để sử dụng trong URL
        file_id = unique_id
        
        # Trả về URL thay vì file
        file_url = url_for('get_file', file_id=file_id, filename=output_filename, _external=True)
        download_url = url_for('download_single_file', file_id=file_id, filename=output_filename, _external=True)
        
        return jsonify({
            'success': True,
            'message': 'PDF đã được redact thành công',
            'original_filename': original_filename,
            'file_id': file_id,
            'file_url': file_url,
            'download_url': download_url
        })
        
    except Exception as e:
        return jsonify({'error': f'Lỗi xử lý: {str(e)}'}), 500
    finally:
        # Xóa file upload sau khi xử lý xong
        try:
            if os.path.exists(upload_path):
                os.remove(upload_path)
        except:
            pass

@app.route('/get-file/<file_id>/<filename>', methods=['GET'])
def get_file(file_id, filename):
    """
    API endpoint để xem file đã redact
    """
    secure_name = secure_filename(filename)
    file_path = os.path.join(app.config['RESULT_FOLDER'], secure_name)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File không tồn tại'}), 404
    
    return send_file(
        file_path,
        mimetype='application/pdf'
    )

@app.route('/download-file/<file_id>/<filename>', methods=['GET'])
def download_single_file(file_id, filename):
    """
    API endpoint để tải xuống file đã redact
    """
    secure_name = secure_filename(filename)
    file_path = os.path.join(app.config['RESULT_FOLDER'], secure_name)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File không tồn tại'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.route('/batch', methods=['POST'])
def batch_redact():
    """
    API endpoint để redact nhiều file PDF
    
    Form data:
    - files: Nhiều file PDF cần redact
    - dpi: (tùy chọn) DPI cho việc xử lý, mặc định là 300
    
    Trả về danh sách các file đã redact hoặc lỗi
    """
    # Kiểm tra xem request có files không
    if 'files' not in request.files:
        return jsonify({'error': 'Không tìm thấy files trong request'}), 400
    
    files = request.files.getlist('files')
    
    # Kiểm tra có file nào không
    if not files or files[0].filename == '':
        return jsonify({'error': 'Không có file nào được chọn'}), 400
    
    # Lấy DPI từ form data, mặc định là 300
    dpi = int(request.form.get('dpi', 300))
    
    # Tạo thư mục tạm thời để lưu kết quả
    batch_id = str(uuid.uuid4())
    batch_result_dir = os.path.join(app.config['RESULT_FOLDER'], f"batch_{batch_id}")
    os.makedirs(batch_result_dir, exist_ok=True)
    
    results = []
    
    # Xử lý từng file
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            results.append({
                'filename': file.filename,
                'success': False,
                'error': 'Chỉ chấp nhận file PDF'
            })
            continue
            
        try:
            # Tạo tên file độc nhất
            original_filename = secure_filename(file.filename)
            base_filename, _ = os.path.splitext(original_filename)
            
            # Lưu file upload
            unique_id = str(uuid.uuid4())
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{original_filename}")
            file.save(upload_path)
            
            # Đường dẫn file đầu ra
            output_filename = f"{base_filename}_redacted.pdf"
            output_path = os.path.join(batch_result_dir, output_filename)
            
            # Thực hiện redact PDF
            redactor = PDFRedactor(upload_path, output_path, dpi)
            result_path = redactor.process()
            
            if result_path:
                # Tạo URL cho file
                view_url = url_for('view_batch_file', batch_id=batch_id, filename=output_filename, _external=True)
                download_url = url_for('download_file', batch_id=batch_id, filename=output_filename, _external=True)
                
                results.append({
                    'filename': file.filename,
                    'success': True,
                    'redacted_file': output_filename,
                    'view_url': view_url,
                    'download_url': download_url
                })
            else:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': 'Lỗi khi xử lý file'
                })
                
        except Exception as e:
            results.append({
                'filename': file.filename,
                'success': False,
                'error': str(e)
            })
            
        finally:
            # Xóa file upload
            try:
                if os.path.exists(upload_path):
                    os.remove(upload_path)
            except:
                pass
    
    # Trả về kết quả
    return jsonify({
        'batch_id': batch_id,
        'results': results,
        'message': f'Đã xử lý {len(files)} file PDF'
    })

@app.route('/view/<batch_id>/<filename>', methods=['GET'])
def view_batch_file(batch_id, filename):
    """
    API endpoint để xem file đã redact từ batch processing
    """
    batch_dir = os.path.join(app.config['RESULT_FOLDER'], f"batch_{batch_id}")
    
    if not os.path.exists(batch_dir):
        return jsonify({'error': 'Batch ID không tồn tại'}), 404
    
    file_path = os.path.join(batch_dir, secure_filename(filename))
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File không tồn tại'}), 404
    
    return send_file(
        file_path,
        mimetype='application/pdf'
    )

@app.route('/download/<batch_id>/<filename>', methods=['GET'])
def download_file(batch_id, filename):
    """
    API endpoint để tải file đã redact từ batch processing
    """
    batch_dir = os.path.join(app.config['RESULT_FOLDER'], f"batch_{batch_id}")
    
    if not os.path.exists(batch_dir):
        return jsonify({'error': 'Batch ID không tồn tại'}), 404
    
    file_path = os.path.join(batch_dir, secure_filename(filename))
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File không tồn tại'}), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    print("===== PDF Redactor API =====")
    print("Truy cập API qua: http://localhost:5000")
    print("API endpoints:")
    print("  - GET  /                               : Trang web")
    print("  - GET  /health                         : Kiểm tra API")
    print("  - POST /redact                         : Redact một file PDF")
    print("  - GET  /get-file/{file_id}/{filename}  : Xem file đã redact")
    print("  - GET  /download-file/{file_id}/{filename} : Tải xuống file đã redact")
    print("  - POST /batch                          : Redact nhiều file PDF")
    print("  - GET  /view/{batch_id}/{filename}     : Xem file từ batch")
    print("  - GET  /download/{batch_id}/{filename} : Tải xuống file từ batch")
    print("===========================")
    # Chạy API server
    app.run(host='0.0.0.0', port=5000, debug=True) 