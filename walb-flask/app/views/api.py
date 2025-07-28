"""
REST API 엔드포인트
"""
from flask import Blueprint, jsonify, request, send_file, abort
import os
from app.models.account import AWSAccount
from app.utils.diagnosis_logger import diagnosis_logger

api_bp = Blueprint('api', __name__)

@api_bp.route('/accounts')
def get_accounts():
    """계정 목록 조회"""
    accounts = AWSAccount.load_all()
    return jsonify({
        'accounts': [acc.to_dict() for acc in accounts]
    })

@api_bp.route('/accounts/<account_id>')
def get_account(account_id):
    """특정 계정 조회"""
    account = AWSAccount.find_by_id(account_id)
    if account:
        return jsonify(account.to_dict())
    return jsonify({'error': 'Account not found'}), 404

@api_bp.route('/health')
def health_check():
    """헬스 체크"""
    return jsonify({
        'status': 'ok',
        'message': 'WALB Flask API is running'
    })

@api_bp.route('/diagnosis/logs')
def get_recent_diagnosis_logs():
    """최근 진단 로그 목록 조회"""
    try:
        recent_logs = diagnosis_logger.get_recent_logs(limit=20)
        
        log_list = []
        for log_info in recent_logs:
            log_list.append({
                'filename': log_info['filename'],
                'modified_time': log_info['modified_time'].strftime('%Y-%m-%d %H:%M:%S'),
                'size_mb': round(log_info['size'] / (1024 * 1024), 2)
            })
        
        return jsonify({
            'status': 'success',
            'logs': log_list
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'로그 목록 조회 실패: {str(e)}'
        }), 500

@api_bp.route('/diagnosis/logs/download/<filename>')
def download_diagnosis_log(filename):
    """진단 로그 파일 다운로드"""
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
        return jsonify({
            'status': 'error',
            'message': f'로그 파일 다운로드 실패: {str(e)}'
        }), 500