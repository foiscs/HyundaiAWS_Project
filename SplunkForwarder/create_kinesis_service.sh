#!/bin/bash

show_usage() {
    echo "사용법:"
    echo "  Access Key 모드:"
    echo "    $0 accesskey <account_id> <access_key_id> <secret_access_key> [region]"
    echo ""
    echo "  Cross-Account Role 모드:"
    echo "    $0 role <account_id> <role_arn> [region]"
    echo ""
    echo "예시:"
    echo "  $0 accesskey 253157413163 AKIA... secret... ap-northeast-2"
    echo "  $0 role 253157413163 arn:aws:iam::253157413163:role/KinesisForwarderRole"
    echo ""
    echo "매개변수:"
    echo "  mode: accesskey 또는 role"
    echo "  account_id: AWS 계정 ID"
    echo "  access_key_id: AWS Access Key ID (accesskey 모드에서만 필요)"
    echo "  secret_access_key: AWS Secret Access Key (accesskey 모드에서만 필요)"
    echo "  role_arn: Cross-Account Role ARN (role 모드에서만 필요)"
    echo "  region: AWS 리전 (선택사항, 기본값: ap-northeast-2)"
}

if [ $# -lt 3 ]; then
    show_usage
    exit 1
fi

MODE=$1
ACCOUNT_ID=$2

case $MODE in
        "accesskey")
                if [ $# -lt 4 ]; then
                        echo "error: Access key mode에서 최소 4개 매개변수 필요"
                        show_usage
                        exit 1
                fi
                ACCESS_KEY_ID=$3
                SECRET_ACCESS_KEY=$4
                REGION=${5:-ap-northeast-2}
                ;;
        "role")
                if [ $# -lt 3 ]; then
                        echo "error: Role mode에서 최소 3개의 매개변수 필요"
                        show_usage
                        exit 1
                fi
                ROLE_ARN=$3
                REGION=${4:-ap-northeast-2}
                ;;
        *)
                echo "error : 잘못된 모드입니다. 'accesskey' or 'role'을 선택하세요."
                show_usage
                exit 1
                ;;
esac

SERVICE_NAME="kinesis-splunk-forwarder-${ACCOUNT_ID}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat > ${SERVICE_FILE} << EOF
[Unit]
Description=Kinesis Splunk Forwarder Service for Account ${ACCOUNT_ID}
After=network-online.target SplunkForwarder.service
Wants=network-online.target
Requires=SplunkForwarder.service

[Service]
Type=simple
User=splunk
Group=splunk
WorkingDirectory=/opt
Environment=AWS_DEFAULT_REGION=${REGION}
Environment=AWS_ACCOUNT_ID=${ACCOUNT_ID}
Environment=AUTH_MODE=${MODE}
EOF

# 인증 모드별 환경변수 추가
if [ "$MODE" = "accesskey" ]; then
    cat >> ${SERVICE_FILE} << EOF
Environment=AWS_ACCESS_KEY_ID=${ACCESS_KEY_ID}
Environment=AWS_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}
EOF
    echo "Access Key ID: ${ACCESS_KEY_ID}"
elif [ "$MODE" = "role" ]; then
    cat >> ${SERVICE_FILE} << EOF
Environment=AWS_ROLE_ARN=${ROLE_ARN}
EOF
    echo "Role ARN: ${ROLE_ARN}"
fi

cat >> ${SERVICE_FILE} << EOF
ExecStart=/usr/bin/python3 /opt/kinesis_splunk_forwarder.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 권한 설정
chmod 644 ${SERVICE_FILE}

echo "서비스 파일 생성 완료: ${SERVICE_FILE}"

sudo systemctl daemon-reload

sudo systemctl enable ${SERVICE_FILE}

sudo systemctl restart ${SERVICE_FILE}

sudo systemctl status ${SERVICE_FILE}