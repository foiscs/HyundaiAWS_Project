#!/bin/bash
echo "🚀 WALB Flask 배포 시작..."

# Git pull
echo "📥 코드 업데이트 중..."
if git pull origin main; then
    echo "✅ Git pull 성공"
else
    echo "❌ Git pull 실패"
    exit 1
fi

# 서비스 재시작
echo "🔄 서비스 재시작 중..."
sudo systemctl restart walb-flask

# 잠시 대기
sleep 2

# 상태 확인
if sudo systemctl is-active --quiet walb-flask; then
    echo "✅ 서비스 상태: 정상 실행 중"
    echo "🎉 배포 완료!"
    echo "🌐 접속: http://3.39.158.137"
else
    echo "❌ 서비스 시작 실패"
    sudo systemctl status walb-flask
fi
