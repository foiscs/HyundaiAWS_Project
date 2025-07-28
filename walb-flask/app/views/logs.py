"""
로그 조회 관련 뷰 - 진단 로그 조회 및 다운로드
"""
from flask import Blueprint, render_template, request, jsonify, send_file, abort
import os
from datetime import datetime
from app.utils.diagnosis_logger import diagnosis_logger

logs_bp = Blueprint('logs', __name__, url_prefix='/logs')

@logs_bp.route('/')
def index():
    """로그 조회 메인 페이지"""
    return render_template('pages/logs.html')

@logs_bp.route('/api/list')
def list_logs():
    """로그 파일 목록 API"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 전체 로그 목록 조회
        all_logs = diagnosis_logger.get_recent_logs(limit=100)  # 최대 100개
        
        # 페이지네이션
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        logs = all_logs[start_idx:end_idx]
        
        # 로그 정보 포맷팅
        log_list = []
        for log_info in logs:
            # 파일명에서 정보 추출 (예: TestAccount_batch_20240128_153015.log)
            filename = log_info['filename']
            parts = filename.replace('.log', '').split('_')
            
            if len(parts) >= 4:
                account_name = parts[0]
                session_type = parts[1] 
                date_part = parts[2]
                time_part = parts[3]
                
                # 날짜/시간 파싱
                try:
                    session_datetime = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                    formatted_datetime = session_datetime.strftime("%Y년 %m월 %d일 %H:%M")
                except:
                    formatted_datetime = "날짜 파싱 실패"
            else:
                account_name = "알 수 없음"
                session_type = "unknown"
                formatted_datetime = "날짜 파싱 실패"
            
            log_list.append({
                'filename': filename,
                'account_name': account_name,
                'session_type': '전체 진단' if session_type == 'batch' else '개별 진단',
                'created_at': formatted_datetime,
                'modified_time': log_info['modified_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'size_mb': round(log_info['size'] / (1024 * 1024), 2),
                'size_kb': round(log_info['size'] / 1024, 1)
            })
        
        return jsonify({
            'status': 'success',
            'logs': log_list,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_logs': len(all_logs),
                'total_pages': (len(all_logs) + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'로그 목록 조회 실패: {str(e)}'
        }), 500

@logs_bp.route('/api/content/<filename>')
def get_log_content(filename):
    """로그 파일 내용 조회 API"""
    try:
        # 파일명 검증 (보안을 위해)
        if not filename.endswith('.log') or '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'status': 'error',
                'message': '잘못된 파일명입니다.'
            }), 400
        
        log_dir = "logs/diagnosis"
        file_path = os.path.join(log_dir, filename)
        
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': '로그 파일을 찾을 수 없습니다.'
            }), 404
        
        # 파일 크기 제한 (10MB)
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({
                'status': 'error',
                'message': '파일이 너무 큽니다. 다운로드를 이용해주세요.'
            }), 413
        
        # 파일 내용 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8로 읽기 실패시 다른 인코딩 시도
            with open(file_path, 'r', encoding='cp949') as f:
                content = f.read()
        
        # 파일 정보 추출
        stat = os.stat(file_path)
        file_info = {
            'filename': filename,
            'size': file_size,
            'size_formatted': f"{round(file_size / 1024, 1)} KB" if file_size < 1024*1024 else f"{round(file_size / (1024*1024), 2)} MB",
            'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'line_count': len(content.splitlines())
        }
        
        return jsonify({
            'status': 'success',
            'content': content,
            'file_info': file_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'로그 파일 조회 실패: {str(e)}'
        }), 500

@logs_bp.route('/download/<filename>')
def download_log(filename):
    """로그 파일 다운로드"""
    try:
        # 파일명 검증 (보안을 위해)
        if not filename.endswith('.log') or '..' in filename or '/' in filename or '\\' in filename:
            abort(400, description="잘못된 파일명입니다.")
        
        log_dir = "logs/diagnosis"
        file_path = os.path.join(log_dir, filename)
        
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            abort(404, description="로그 파일을 찾을 수 없습니다.")
        
        # 파일 다운로드
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    except Exception as e:
        abort(500, description=f"로그 파일 다운로드 실패: {str(e)}")