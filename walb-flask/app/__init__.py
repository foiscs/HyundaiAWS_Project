"""
Flask 애플리케이션 팩토리
"""
from flask import Flask
import sys
import os
from dotenv import load_dotenv

# .env 파일 로드 (있는 경우)
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

def create_app(config_name='default'):
    """Flask 애플리케이션 생성"""
    import os
    
    # 템플릿과 정적 파일 경로 설정 (상위 디렉토리 기준)
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config.from_object(config[config_name])
    
    # 블루프린트 등록
    from app.views.main import main_bp
    from app.views.connection import connection_bp
    from app.views.diagnosis import diagnosis_bp
    from app.views.api import api_bp
    from app.views.monitoring import bp as monitoring_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(connection_bp, url_prefix='/connection')
    app.register_blueprint(diagnosis_bp, url_prefix='/diagnosis') 
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp)
    
    return app