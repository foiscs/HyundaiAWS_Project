"""
메인 페이지 뷰
"""
from flask import Blueprint, render_template, request, jsonify
from app.models.account import AWSAccount

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """메인 대시보드"""
    accounts = AWSAccount.load_all()
    
    # 새 모델의 get_statistics 메서드 사용
    stats = AWSAccount.get_statistics()
    
    return render_template('pages/index.html', accounts=accounts, stats=stats)

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