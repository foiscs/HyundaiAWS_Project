#!/bin/bash

# SK Shieldus 41개 항목 중 추가 취약점 생성 스크립트
# 메인 스크립트와 함께 실행하여 더 많은 취약점 시나리오 생성

set -e

echo "==========================================="
echo "추가 취약점 시나리오 생성"
echo "==========================================="

TIMESTAMP=$(date +%Y%m%d%H%M%S)
REGION=$(aws configure get region || echo "ap-northeast-2")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ==========================================
# 추가 계정 관리 취약점
# ==========================================

echo -e "\n[추가 계정 관리 취약점]"

# 1.7 루트 계정 사용 시뮬레이션 - 루트 계정처럼 보이는 사용자
echo "1.7 루트 계정 유사 사용자 생성..."
aws iam create-user --user-name root-like-user-$TIMESTAMP 2>/dev/null || true
cat > admin-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "*",
    "Resource": "*"
  }]
}
EOF
aws iam put-user-policy --user-name root-like-user-$TIMESTAMP \
    --policy-name FullAdminAccess --policy-document file://admin-policy.json 2>/dev/null || true

# 1.8 90일 이상된 접근키 시뮬레이션을 위한 다수 사용자 생성
echo "1.8 오래된 접근키를 가진 사용자들 생성..."
for i in {1..3}; do
    aws iam create-user --user-name old-key-user-$i-$TIMESTAMP 2>/dev/null || true
    aws iam create-access-key --user-name old-key-user-$i-$TIMESTAMP 2>/dev/null || true
done

# 1.9 MFA 없는 권한 있는 사용자들
echo "1.9 MFA 없는 관리자 권한 사용자 생성..."
aws iam create-user --user-name admin-no-mfa-$TIMESTAMP 2>/dev/null || true
aws iam attach-user-policy --user-name admin-no-mfa-$TIMESTAMP \
    --policy-arn arn:aws:iam::aws:policy/PowerUserAccess 2>/dev/null || true

# ==========================================
# 추가 권한 관리 취약점
# ==========================================

echo -e "\n[추가 권한 관리 취약점]"

# 2.1 인라인 정책이 있는 EC2 역할들
echo "2.1 인라인 정책이 있는 EC2 역할 생성..."
for service in lambda rds s3; do
    cat > trust-$service.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "$service.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF
    aws iam create-role --role-name vulnerable-$service-role-$TIMESTAMP \
        --assume-role-policy-document file://trust-$service.json 2>/dev/null || true
    
    # 인라인 정책 추가
    cat > inline-$service.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:*", "dynamodb:*", "sns:*"],
    "Resource": "*"
  }]
}
EOF
    aws iam put-role-policy --role-name vulnerable-$service-role-$TIMESTAMP \
        --policy-name inline-overpermission --policy-document file://inline-$service.json 2>/dev/null || true
done

# 2.3 조건 없는 AssumeRole 정책
echo "2.3 조건 없는 AssumeRole 정책 생성..."
cat > assume-role-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sts:AssumeRole",
    "Resource": "*"
  }]
}
EOF
aws iam create-policy --policy-name vulnerable-assume-role-$TIMESTAMP \
    --policy-document file://assume-role-policy.json 2>/dev/null || true

# ==========================================
# 추가 가상 자원 취약점
# ==========================================

echo -e "\n[추가 가상 자원 취약점]"

# 기존 VPC ID 가져오기 (메인 스크립트에서 생성된 것 사용)
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=vulnerable-vpc-*" \
    --query 'Vpcs[0].VpcId' --output text 2>/dev/null)

if [ "$VPC_ID" != "None" ] && [ ! -z "$VPC_ID" ]; then
    # 3.2 더 많은 불필요한 포트 개방
    echo "3.2 추가 불필요 포트 개방..."
    SG_EXTRA=$(aws ec2 create-security-group --group-name vulnerable-sg-extra-$TIMESTAMP \
        --description "Extra vulnerable ports" --vpc-id $VPC_ID --query 'GroupId' --output text)
    
    # 위험한 포트들 개방
    DANGEROUS_PORTS=(139 3389 5432 3306 1433 6379 9200 27017 5984)
    for port in "${DANGEROUS_PORTS[@]}"; do
        aws ec2 authorize-security-group-ingress --group-id $SG_EXTRA \
            --protocol tcp --port $port --source 0.0.0.0/0 2>/dev/null || true
    done
    
    # 3.3 NACL 규칙 번호 충돌
    echo "3.3 NACL 규칙 추가..."
    NACL_ID=$(aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
        --query 'NetworkAcls[0].NetworkAclId' --output text)
    
    # 여러 개의 허용 규칙 (우선순위 충돌)
    for i in {110..150..10}; do
        aws ec2 create-network-acl-entry --network-acl-id $NACL_ID \
            --rule-number $i --protocol tcp --rule-action allow \
            --ingress --cidr-block 0.0.0.0/0 --port-range From=1,To=65535 2>/dev/null || true
    done
fi

# 3.7 추가 취약한 S3 버킷들
echo "3.7 추가 취약한 S3 버킷 생성..."
for purpose in logs backup data; do
    BUCKET="vulnerable-$purpose-$ACCOUNT_ID-$TIMESTAMP"
    aws s3 mb s3://$BUCKET --region $REGION 2>/dev/null || true
    
    # 버킷 ACL 설정 (public-read)
    aws s3api put-bucket-acl --bucket $BUCKET --acl public-read 2>/dev/null || true
    
    # 버킷 정책으로 쓰기 권한도 부여
    if [ "$purpose" = "logs" ]; then
        cat > bucket-write-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicWrite",
    "Effect": "Allow",
    "Principal": "*",
    "Action": ["s3:PutObject", "s3:DeleteObject"],
    "Resource": "arn:aws:s3:::$BUCKET/*"
  }]
}
EOF
        aws s3api put-bucket-policy --bucket $BUCKET --policy file://bucket-write-policy.json 2>/dev/null || true
    fi
done

# ==========================================
# 추가 운영 관리 취약점
# ==========================================

echo -e "\n[추가 운영 관리 취약점]"

# 4.5 여러 CloudTrail 비활성화
echo "4.5 여러 CloudTrail 생성 후 비활성화..."
for i in {1..3}; do
    TRAIL_NAME="vulnerable-trail-$i-$TIMESTAMP"
    aws cloudtrail create-trail --name $TRAIL_NAME \
        --s3-bucket-name vulnerable-logs-$ACCOUNT_ID-$TIMESTAMP 2>/dev/null || true
    aws cloudtrail stop-logging --name $TRAIL_NAME 2>/dev/null || true
done

# 4.6 다양한 CloudWatch 로그 그룹 (암호화 없음)
echo "4.6 암호화 없는 CloudWatch 로그 그룹들..."
LOG_GROUPS=("/aws/lambda/vulnerable" "/aws/rds/vulnerable" "/aws/ecs/vulnerable" "/custom/app/vulnerable")
for lg in "${LOG_GROUPS[@]}"; do
    aws logs create-log-group --log-group-name $lg-$TIMESTAMP 2>/dev/null || true
done

# 4.10 S3 버킷 로깅 비활성화 확인
echo "4.10 S3 버킷 로깅 명시적 비활성화..."
for bucket in $(aws s3api list-buckets --query "Buckets[?contains(Name, 'vulnerable')].Name" --output text); do
    aws s3api put-bucket-logging --bucket $bucket --bucket-logging-status '{}' 2>/dev/null || true
done

# 4.12 다양한 로그 보존 기간 설정
echo "4.12 짧은 로그 보존 기간 설정..."
for lg in $(aws logs describe-log-groups --log-group-name-prefix "/aws/vulnerable" \
    --query 'logGroups[*].logGroupName' --output text); do
    # 1일 또는 3일로 설정
    DAYS=$((RANDOM % 2 == 0 ? 1 : 3))
    aws logs put-retention-policy --log-group-name $lg --retention-in-days $DAYS 2>/dev/null || true
done

# ==========================================
# SNS/SQS 추가 취약점
# ==========================================

echo -e "\n[SNS/SQS 추가 취약점]"

# SNS 토픽 with 퍼블릭 구독 허용
echo "퍼블릭 SNS 토픽 생성..."
TOPIC_ARN=$(aws sns create-topic --name vulnerable-topic-$TIMESTAMP --query 'TopicArn' --output text)
cat > sns-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicSubscribe",
    "Effect": "Allow",
    "Principal": "*",
    "Action": ["SNS:Subscribe", "SNS:Publish"],
    "Resource": "$TOPIC_ARN"
  }]
}
EOF
aws sns set-topic-attributes --topic-arn $TOPIC_ARN \
    --attribute-name Policy --attribute-value file://sns-policy.json 2>/dev/null || true

# SQS 큐 with 퍼블릭 접근
echo "퍼블릭 SQS 큐 생성..."
QUEUE_URL=$(aws sqs create-queue --queue-name vulnerable-queue-$TIMESTAMP --query 'QueueUrl' --output text)
cat > sqs-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicAccess",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "SQS:*",
    "Resource": "*"
  }]
}
EOF
aws sqs set-queue-attributes --queue-url $QUEUE_URL \
    --attributes Policy=file://sqs-policy.json 2>/dev/null || true

# ==========================================
# KMS 키 취약 설정
# ==========================================

echo -e "\n[KMS 추가 취약점]"

# 과도한 권한의 KMS 키
echo "취약한 KMS 키 정책..."
cat > kms-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "Enable IAM User Permissions",
    "Effect": "Allow",
    "Principal": {"AWS": "*"},
    "Action": "kms:*",
    "Resource": "*"
  }]
}
EOF

# ==========================================
# Lambda 함수 취약점
# ==========================================

echo -e "\n[Lambda 추가 취약점]"

# Lambda 실행 역할 생성
cat > lambda-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role --role-name vulnerable-lambda-role-$TIMESTAMP \
    --assume-role-policy-document file://lambda-trust.json 2>/dev/null || true

# Lambda 함수용 과도한 권한
aws iam attach-role-policy --role-name vulnerable-lambda-role-$TIMESTAMP \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true

# ==========================================
# 완료 메시지
# ==========================================

echo -e "\n==========================================="
echo "추가 취약점 생성 완료!"
echo "==========================================="
echo "생성된 추가 취약점:"
echo "- 루트 유사 사용자"
echo "- 오래된 접근키 사용자 3명"
echo "- MFA 없는 관리자"
echo "- 인라인 정책 역할들"
echo "- 추가 보안그룹 (위험 포트)"
echo "- 퍼블릭 S3 버킷들"
echo "- 비활성화된 CloudTrail들"
echo "- 퍼블릭 SNS/SQS"
echo "==========================================="

# 임시 파일 정리
rm -f *.json