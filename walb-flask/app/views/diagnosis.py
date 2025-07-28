"""
진단 관련 뷰 - SK Shieldus 41개 보안 진단
"""
from flask import Blueprint, render_template, request, jsonify, session # type: ignore
from app.models.account import AWSAccount
from app.services.diagnosis_service import DiagnosisService
from app.config.diagnosis_config import DiagnosisConfig

diagnosis_bp = Blueprint('diagnosis', __name__)

@diagnosis_bp.route('/')
def index():
    """보안 진단 메인 페이지"""
    # 등록된 계정 목록 조회 (연결 성공한 계정만 표시)
    all_accounts = AWSAccount.load_all()
    accounts = [account for account in all_accounts if account.status == 'active']
    failed_accounts_count = len([account for account in all_accounts if account.status == 'failed'])
    
    # 진단 설정 데이터 가져오기
    config = DiagnosisConfig()
    sk_items = config.get_sk_shieldus_items()
    stats = config.get_severity_stats()
    
    # 선택된 계정 (쿼리 파라미터에서)
    selected_account_id = request.args.get('account')
    selected_account = None
    if selected_account_id:
        selected_account = AWSAccount.find_by_id(selected_account_id)
        # 선택된 계정이 연결 실패 상태라면 None으로 설정
        if selected_account and selected_account.status != 'active':
            selected_account = None
    
    return render_template('pages/diagnosis.html', 
                         accounts=accounts,
                         selected_account=selected_account,
                         sk_items=sk_items,
                         stats=stats,
                         failed_accounts_count=failed_accounts_count)

@diagnosis_bp.route('/api/run', methods=['POST'])
def run_diagnosis():
    """개별 진단 실행 API"""
    try:
        print(f"[DEBUG] 진단 API 호출됨")
        data = request.get_json()
        print(f"[DEBUG] 요청 데이터: {data}")
        
        account_id = data.get('account_id')
        item_code = data.get('item_code')
        
        if not account_id or not item_code:
            print(f"[DEBUG] 필수 파라미터 누락: account_id={account_id}, item_code={item_code}")
            return jsonify({
                'status': 'error',
                'message': '계정 ID와 진단 항목 코드가 필요합니다.'
            }), 400
        
        # 계정 정보 조회
        account = AWSAccount.find_by_id(account_id)
        if not account:
            print(f"[DEBUG] 계정 조회 실패: {account_id}")
            return jsonify({
                'status': 'error',
                'message': '계정을 찾을 수 없습니다.'
            }), 404
        
        print(f"[DEBUG] 계정 조회 성공: {account.cloud_name}")
        
        # 진단 서비스 초기화
        diagnosis_service = DiagnosisService()
        
        # 진단 실행
        print(f"[DEBUG] 진단 실행 시작: {item_code}")
        result = diagnosis_service.run_single_diagnosis(account, item_code)
        print(f"[DEBUG] 진단 실행 완료: {result['status']}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[DEBUG] 진단 API 오류: {str(e)}")
        import traceback
        traceback.print_exc()
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
        
        # 전체 진단 실행 (로깅 활성화)
        result = diagnosis_service.run_batch_diagnosis(account, enable_logging=True)
        
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