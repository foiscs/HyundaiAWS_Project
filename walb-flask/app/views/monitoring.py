"""
모니터링 뷰
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models.account import AWSAccount
from app.services.kinesis_service import KinesisServiceManager
from app.services.splunk_service import SplunkService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

# 서비스 인스턴스 초기화
kinesis_manager = KinesisServiceManager()
splunk_service = SplunkService()

@bp.route('/')
def index():
    """모니터링 메인 페이지"""
    # URL 파라미터에서 계정 ID 가져오기
    account_id = request.args.get('account')
    
    # 등록된 계정 목록 가져오기
    accounts = AWSAccount.load_all()
    
    # 선택된 계정 정보
    selected_account = None
    service_status = None
    monitoring_status = None
    
    if account_id:
        selected_account = AWSAccount.find_by_id(account_id)
        if selected_account:
            # Kinesis 서비스 상태 확인
            service_status = kinesis_manager.get_service_status(account_id)
            # Splunk 모니터링 상태 확인
            monitoring_status = splunk_service.get_account_monitoring_status(account_id)
    
    return render_template('pages/monitoring.html', 
                         accounts=accounts,
                         selected_account=selected_account,
                         service_status=service_status,
                         monitoring_status=monitoring_status)

@bp.route('/service/create', methods=['POST'])
def create_service():
    """Kinesis 서비스 생성"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    account = AWSAccount.find_by_id(account_id)
    if not account:
        return jsonify({"success": False, "message": "계정을 찾을 수 없습니다"}), 404
    
    try:
        result = kinesis_manager.create_kinesis_service(account)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        return jsonify({"success": False, "message": f"서비스 생성 중 오류: {str(e)}"}), 500

@bp.route('/service/start', methods=['POST'])
def start_service():
    """Kinesis 서비스 시작"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    try:
        result = kinesis_manager.start_kinesis_service(account_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting service: {e}")
        return jsonify({"success": False, "message": f"서비스 시작 중 오류: {str(e)}"}), 500

@bp.route('/service/stop', methods=['POST'])
def stop_service():
    """Kinesis 서비스 중지"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    try:
        result = kinesis_manager.stop_kinesis_service(account_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping service: {e}")
        return jsonify({"success": False, "message": f"서비스 중지 중 오류: {str(e)}"}), 500

@bp.route('/service/remove', methods=['POST'])
def remove_service():
    """Kinesis 서비스 제거"""
    account_id = request.form.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "계정 ID가 필요합니다"}), 400
    
    try:
        result = kinesis_manager.remove_kinesis_service(account_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error removing service: {e}")
        return jsonify({"success": False, "message": f"서비스 제거 중 오류: {str(e)}"}), 500

@bp.route('/service/status/<account_id>')
def get_service_status(account_id):
    """서비스 상태 조회 (AJAX)"""
    try:
        status = kinesis_manager.get_service_status(account_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/service/logs/<account_id>')
def get_service_logs(account_id):
    """서비스 로그 조회"""
    lines = request.args.get('lines', 50, type=int)
    
    try:
        logs = kinesis_manager.get_service_logs(account_id, lines)
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Error getting service logs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route('/splunk/redirect/<account_id>')
def splunk_redirect(account_id):
    """Splunk 웹으로 리다이렉션"""
    log_type = request.args.get('log_type', 'cloudtrail')
    search_term = request.args.get('search', '*')
    time_range = request.args.get('time', '-24h')
    
    try:
        if search_term and search_term != '*':
            splunk_url = splunk_service.create_custom_search_url(
                account_id=account_id,
                custom_query=search_term,
                time_range=time_range
            )
        else:
            splunk_url = splunk_service.generate_splunk_search_url(
                account_id=account_id,
                log_type=log_type,
                search_term='*',
                earliest_time=time_range
            )
        
        logger.info(f"Redirecting to Splunk for account {account_id}: {splunk_url}")
        return redirect(splunk_url)
        
    except Exception as e:
        logger.error(f"Error generating Splunk URL: {e}")
        return jsonify({"error": f"Splunk URL 생성 오류: {str(e)}"}), 500

@bp.route('/splunk/urls/<account_id>')
def get_splunk_urls(account_id):
    """계정별 Splunk URL 조회 (AJAX)"""
    try:
        urls = splunk_service.get_splunk_dashboard_urls(account_id)
        return jsonify(urls)
    except Exception as e:
        logger.error(f"Error getting Splunk URLs: {e}")
        return jsonify({"error": str(e)}), 500