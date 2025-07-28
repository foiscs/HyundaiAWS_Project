"""
메인 페이지 뷰
"""
from flask import Blueprint, render_template, request, jsonify, current_app # type: ignore
from app.models.account import AWSAccount
from app.utils.aws_handler import AWSConnectionHandler
import json
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """메인 대시보드"""
    accounts = AWSAccount.load_all()
    
    # 새 모델의 get_statistics 메서드 사용
    stats = AWSAccount.get_statistics()
    
    return render_template('pages/index.html', accounts=accounts, stats=stats)

@main_bp.route('/api/test-all-connections', methods=['POST'])
def test_all_connections():
    """모든 계정의 연결 상태 테스트"""
    try:
        # 모든 계정 로드
        accounts = AWSAccount.load_all()
        
        if not accounts:
            return jsonify({
                'success': True,
                'message': '등록된 계정이 없습니다.',
                'results': {}
            })
        
        aws_handler = AWSConnectionHandler()
        results = {}
        
        for account in accounts:
            account_key = f"{account.account_id}_{account.cloud_name}"
            
            try:
                # 연결 방식에 따라 테스트 수행
                if account.connection_type == 'role':
                    # Cross-Account Role 테스트
                    test_result = aws_handler.test_cross_account_connection(
                        role_arn=account.role_arn,
                        external_id=account.external_id,
                        region=account.primary_region
                    )
                else:
                    # Access Key 테스트
                    test_result = aws_handler.test_access_key_connection(
                        access_key_id=account.access_key_id,
                        secret_access_key=account.secret_access_key,
                        region=account.primary_region
                    )
                
                # 연결 상태 업데이트
                if test_result.get('status') == 'success':
                    new_status = 'active'
                    status_message = '연결됨'
                else:
                    new_status = 'failed'
                    status_message = '연결실패'
                
                # 계정 상태 업데이트 (파일에 저장)
                _update_account_status(account, new_status)
                
                results[account_key] = {
                    'account_id': account.account_id,
                    'cloud_name': account.cloud_name,
                    'connection_type': account.connection_type,
                    'old_status': account.status,
                    'new_status': new_status,
                    'status_message': status_message,
                    'test_success': test_result.get('status') == 'success',
                    'error_message': test_result.get('error_message') if test_result.get('status') != 'success' else None
                }
                
            except Exception as e:
                # 개별 계정 테스트 실패
                _update_account_status(account, 'failed')
                
                results[account_key] = {
                    'account_id': account.account_id,
                    'cloud_name': account.cloud_name,
                    'connection_type': account.connection_type,
                    'old_status': account.status,
                    'new_status': 'failed',
                    'status_message': '연결실패',
                    'test_success': False,
                    'error_message': str(e)
                }
        
        return jsonify({
            'success': True,
            'message': f'{len(accounts)}개 계정의 연결 상태를 확인했습니다.',
            'total_accounts': len(accounts),
            'results': results
        })
        
    except Exception as e:
        current_app.logger.error(f"전체 계정 연결 테스트 오류: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'연결 테스트 중 오류가 발생했습니다: {str(e)}'
        }), 500

def _update_account_status(account, new_status):
    """계정 상태를 파일에 업데이트"""
    try:
        accounts_file = current_app.config['ACCOUNTS_FILE']
        
        # 기존 계정들 로드
        existing_accounts = []
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        account_data = json.loads(line.strip())
                        # 현재 계정과 일치하면 상태 업데이트
                        if (account_data.get('account_id') == account.account_id and 
                            account_data.get('cloud_name') == account.cloud_name):
                            account_data['status'] = new_status
                        existing_accounts.append(account_data)
        
        # 파일에 다시 저장
        with open(accounts_file, 'w', encoding='utf-8') as f:
            for account_data in existing_accounts:
                f.write(json.dumps(account_data, ensure_ascii=False) + '\n')
                
    except Exception as e:
        current_app.logger.error(f"계정 상태 업데이트 실패: {str(e)}")

@main_bp.route('/api/accounts/delete', methods=['POST'])
def delete_account():
    """AWS 계정 삭제 API"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '요청 데이터가 없습니다.'
            }), 400
        
        account_id = data.get('account_id')
        cloud_name = data.get('cloud_name')
        
        if not account_id or not cloud_name:
            return jsonify({
                'success': False,
                'error': '계정 ID와 클라우드 이름이 필요합니다.'
            }), 400
        
        # 계정 찾기
        account = AWSAccount.find_by_id_and_name(account_id, cloud_name)
        
        if not account:
            return jsonify({
                'success': False,
                'error': f'계정을 찾을 수 없습니다. (ID: {account_id}, 이름: {cloud_name})'
            }), 404
        
        # 계정 삭제
        account.delete()
        
        return jsonify({
            'success': True,
            'message': f'"{cloud_name}" 계정이 성공적으로 삭제되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'계정 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500