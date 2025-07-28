"""
모니터링 뷰
"""

from flask import Blueprint, render_template, request
from app.models.account import AWSAccount

bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@bp.route('/')
def index():
    """모니터링 메인 페이지"""
    # URL 파라미터에서 계정 ID 가져오기
    account_id = request.args.get('account')
    
    # 등록된 계정 목록 가져오기
    accounts = AWSAccount.load_all()
    
    # 선택된 계정 정보
    selected_account = None
    if account_id:
        selected_account = AWSAccount.find_by_id(account_id)
    
    return render_template('pages/monitoring.html', 
                         accounts=accounts,
                         selected_account=selected_account)