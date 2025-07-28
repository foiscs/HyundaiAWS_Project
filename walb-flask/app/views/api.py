"""
REST API 엔드포인트
"""
from flask import Blueprint, jsonify, request
from app.models.account import AWSAccount

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