"""
Flask 개발 서버 실행 스크립트
"""
import os
from app import create_app

# 환경 설정
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == '__main__':
    print("WALB Flask 개발 서버를 시작합니다...")
    print("URL: http://127.0.0.1:5000")
    print(f"환경: {config_name}")
    print("Templates 경로:", app.template_folder)
    print("Static 경로:", app.static_folder)
    app.run(host='127.0.0.1', port=5000, debug=True)