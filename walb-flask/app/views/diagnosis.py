"""
진단 관련 뷰 - SK Shieldus 41개 보안 진단
"""
from flask import Blueprint, render_template, request, jsonify, session
from app.models.account import AWSAccount
from app.services.diagnosis_service import DiagnosisService
from app.config.diagnosis_config import DiagnosisConfig

diagnosis_bp = Blueprint('diagnosis', __name__)

@diagnosis_bp.route('/')
def index():
    """보안 진단 메인 페이지"""
    # 등록된 계정 목록 조회
    accounts = AWSAccount.load_all()
    
    # 진단 설정 데이터 가져오기
    config = DiagnosisConfig()
    sk_items = config.get_sk_shieldus_items()
    stats = config.get_severity_stats()
    
    # 선택된 계정 (쿼리 파라미터에서)
    selected_account_id = request.args.get('account')
    selected_account = None
    if selected_account_id:
        selected_account = AWSAccount.find_by_id(selected_account_id)
    
    return render_template('pages/diagnosis.html', 
                         accounts=accounts,
                         selected_account=selected_account,
                         sk_items=sk_items,
                         stats=stats)

@diagnosis_bp.route('/api/run', methods=['POST'])
def run_diagnosis():
    """개별 진단 실행 API"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        item_code = data.get('item_code')
        
        if not account_id or not item_code:
            return jsonify({
                'status': 'error',
                'message': '계정 ID와 진단 항목 코드가 필요합니다.'
            }), 400
        
        # 계정 정보 조회
        account = AWSAccount.find_by_id(account_id)
        if not account:
            return jsonify({
                'status': 'error',
                'message': '계정을 찾을 수 없습니다.'
            }), 404
        
        # 진단 서비스 초기화
        diagnosis_service = DiagnosisService()
        
        # 진단 실행
        result = diagnosis_service.run_single_diagnosis(account, item_code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@diagnosis_bp.route('/api/run-all', methods=['POST'])
def run_all_diagnosis():
    """전체 진단 실행 API"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({
                'status': 'error',
                'message': '계정 ID가 필요합니다.'
            }), 400
        
        # 계정 정보 조회
        account = AWSAccount.find_by_id(account_id)
        if not account:
            return jsonify({
                'status': 'error',
                'message': '계정을 찾을 수 없습니다.'
            }), 404
        
        # 진단 서비스 초기화
        diagnosis_service = DiagnosisService()
        
        # 전체 진단 실행
        result = diagnosis_service.run_batch_diagnosis(account)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@diagnosis_bp.route('/api/fix', methods=['POST'])
def execute_fix():
    """자동 조치 실행 API"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        item_code = data.get('item_code')
        selected_items = data.get('selected_items', {})
        
        if not account_id or not item_code:
            return jsonify({
                'status': 'error',
                'message': '계정 ID와 진단 항목 코드가 필요합니다.'
            }), 400
        
        # 계정 정보 조회
        account = AWSAccount.find_by_id(account_id)
        if not account:
            return jsonify({
                'status': 'error',
                'message': '계정을 찾을 수 없습니다.'
            }), 404
        
        # 진단 서비스 초기화
        diagnosis_service = DiagnosisService()
        
        # 조치 실행
        result = diagnosis_service.execute_fix(account, item_code, selected_items)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@diagnosis_bp.route('/api/test-session', methods=['POST'])
def test_session():
    """AWS 세션 연결 테스트 API"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({
                'status': 'error',
                'message': '계정 ID가 필요합니다.'
            }), 400
        
        # 계정 정보 조회
        account = AWSAccount.find_by_id(account_id)
        if not account:
            return jsonify({
                'status': 'error',
                'message': '계정을 찾을 수 없습니다.'
            }), 404
        
        # 진단 서비스 초기화
        diagnosis_service = DiagnosisService()
        
        # 세션 테스트
        result = diagnosis_service.test_aws_session(account)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500