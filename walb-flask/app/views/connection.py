"""
AWS 계정 연결 뷰 - mainHub connection 모듈 이식
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app # type: ignore
from app.models.account import AWSAccount
from app.utils.aws_handler import AWSConnectionHandler, InputValidator

connection_bp = Blueprint('connection', __name__)

@connection_bp.route('/')
def index():
    """계정 연결 페이지"""
    # 수정 모드 확인
    mode = request.args.get('mode')
    account_id = request.args.get('account')
    cloud_name = request.args.get('name')
    
    edit_account = None
    if mode == 'edit' and account_id and cloud_name:
        # 수정할 계정 정보 조회
        edit_account = AWSAccount.find_by_id_and_name(account_id, cloud_name)
        if not edit_account:
            # 계정을 찾을 수 없으면 일반 연결 모드로 fallback
            mode = None
    
    return render_template('pages/connection.html', 
                         edit_mode=(mode == 'edit'),
                         edit_account=edit_account)

@connection_bp.route('/test', methods=['POST'])
def test_connection():
    """연결 테스트 - mainHub와 동일한 로직"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '요청 데이터가 없습니다.'
            }), 400
        
        aws_handler = AWSConnectionHandler()
        connection_type = data.get('connection_type')
        
        if connection_type == 'role':
            # Cross-Account Role 테스트
            role_arn = data.get('role_arn', '').strip()
            external_id = data.get('external_id', '').strip()
            region = data.get('primary_region', 'ap-northeast-2')
            
            # 입력값 검증
            validator = InputValidator()
            is_valid_arn, arn_msg = validator.validate_role_arn(role_arn)
            if not is_valid_arn:
                return jsonify({
                    'success': False,
                    'error': arn_msg
                }), 400
            
            # 연결 테스트 실행
            result = aws_handler.test_cross_account_connection(role_arn, external_id, region)
            
        elif connection_type == 'access_key':
            # Access Key 테스트
            access_key_id = data.get('access_key_id', '').strip()
            secret_access_key = data.get('secret_access_key', '').strip()
            region = data.get('primary_region', 'ap-northeast-2')
            
            # 입력값 검증
            validator = InputValidator()
            is_valid_key, key_msg = validator.validate_access_key(access_key_id)
            if not is_valid_key:
                return jsonify({
                    'success': False,
                    'error': key_msg
                }), 400
            
            is_valid_secret, secret_msg = validator.validate_secret_key(secret_access_key)
            if not is_valid_secret:
                return jsonify({
                    'success': False,
                    'error': secret_msg
                }), 400
            
            # 연결 테스트 실행
            result = aws_handler.test_access_key_connection(access_key_id, secret_access_key, region)
            
        else:
            return jsonify({
                'success': False,
                'error': '올바르지 않은 연결 방식입니다.'
            }), 400
        
        # 결과 반환
        if result.get('status') == 'success':
            return jsonify({
                'success': True,
                'message': '연결 테스트 성공',
                'test_result': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error_message', '연결 테스트 실패')
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"연결 테스트 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'연결 테스트 중 오류가 발생했습니다: {str(e)}'
        }), 500

@connection_bp.route('/save', methods=['POST'])
def save_account():
    """계정 저장 - mainHub와 동일한 로직"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '요청 데이터가 없습니다.'
            }), 400
        
        # 계정 객체 생성
        account = AWSAccount(data)
        
        # 데이터 검증
        is_valid, error_msg = account.validate()
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # 중복 확인
        existing_account = AWSAccount.find_by_id_and_name(
            account.account_id, 
            account.cloud_name
        )
        
        if existing_account:
            return jsonify({
                'success': False,
                'error': f'이미 등록된 계정입니다. (계정 ID: {account.account_id}, 이름: {account.cloud_name})'
            }), 400
        
        # 계정 저장
        account.save()
        
        current_app.logger.info(f"새 계정 등록 성공: {account.cloud_name} ({account.account_id})")
        
        return jsonify({
            'success': True,
            'message': '계정이 성공적으로 저장되었습니다.',
            'account': {
                'cloud_name': account.cloud_name,
                'account_id': account.account_id,
                'connection_type': account.connection_type
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"계정 저장 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'계정 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500

@connection_bp.route('/update', methods=['POST'])
def update_account():
    """계정 수정"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '요청 데이터가 없습니다.'
            }), 400
        
        original_account_id = data.get('original_account_id')
        if not original_account_id:
            return jsonify({
                'success': False,
                'error': '원본 계정 ID가 필요합니다.'
            }), 400
        
        # 수정할 계정 데이터에서 original_account_id 제거
        update_data = {k: v for k, v in data.items() if k != 'original_account_id'}
        
        # 새 계정 객체 생성
        updated_account = AWSAccount(update_data)
        
        # 데이터 검증
        is_valid, error_msg = updated_account.validate()
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # 기존 계정을 다른 이름/ID로 변경하는 경우 중복 확인
        original_cloud_name = None
        # 기존 계정의 cloud_name을 찾기 위해
        original_account = AWSAccount.find_by_id(original_account_id)
        if original_account:
            original_cloud_name = original_account.cloud_name
            
        if (updated_account.account_id != original_account_id or 
            updated_account.cloud_name != original_cloud_name):
            
            existing_account = AWSAccount.find_by_id_and_name(
                updated_account.account_id, 
                updated_account.cloud_name
            )
            
            if existing_account:
                return jsonify({
                    'success': False,
                    'error': f'이미 등록된 계정입니다. (계정 ID: {updated_account.account_id}, 이름: {updated_account.cloud_name})'
                }), 400
        
        # 기존 계정 삭제 후 새 계정으로 저장
        success = AWSAccount.delete_by_account_id(original_account_id)
        if not success:
            return jsonify({
                'success': False,
                'error': '기존 계정을 찾을 수 없습니다.'
            }), 404
        
        # 새 계정 저장
        updated_account.save()
        
        current_app.logger.info(f"계정 수정 성공: {updated_account.cloud_name} ({updated_account.account_id})")
        
        return jsonify({
            'success': True,
            'message': '계정이 성공적으로 수정되었습니다.',
            'account': {
                'cloud_name': updated_account.cloud_name,
                'account_id': updated_account.account_id,
                'connection_type': updated_account.connection_type
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"계정 수정 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'계정 수정 중 오류가 발생했습니다: {str(e)}'
        }), 500

@connection_bp.route('/policies', methods=['GET'])
def get_policies():
    """IAM 정책 생성 - mainHub connection_engine과 동일"""
    try:
        aws_handler = AWSConnectionHandler()
        external_id = aws_handler.generate_external_id()
        
        trust_policy = aws_handler.generate_trust_policy(external_id)
        permission_policy = aws_handler.generate_permission_policy()
        
        return jsonify({
            'success': True,
            'external_id': external_id,
            'trust_policy': trust_policy,
            'permission_policy': permission_policy,
            'walb_account_id': aws_handler.walb_service_account_id
        })
        
    except Exception as e:
        current_app.logger.error(f"정책 생성 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'정책 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@connection_bp.route('/validate', methods=['POST'])  
def validate_field():
    """입력 필드 검증 - mainHub connection_engine과 동일"""
    try:
        data = request.get_json()
        field_type = data.get('field_type')
        value = data.get('value', '').strip()
        
        validator = InputValidator()
        
        if field_type == 'account_id':
            is_valid, message = validator.validate_account_id(value)
        elif field_type == 'role_arn':
            is_valid, message = validator.validate_role_arn(value)
        elif field_type == 'access_key':
            is_valid, message = validator.validate_access_key(value)
        elif field_type == 'secret_key':
            is_valid, message = validator.validate_secret_key(value)
        elif field_type == 'email':
            is_valid, message = validator.validate_email(value)
        else:
            return jsonify({
                'success': False,
                'error': '지원하지 않는 필드 타입입니다.'
            }), 400
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'message': message
        })
        
    except Exception as e:
        current_app.logger.error(f"필드 검증 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'필드 검증 중 오류가 발생했습니다: {str(e)}'
        }), 500