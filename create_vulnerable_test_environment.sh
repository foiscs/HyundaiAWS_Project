#!/bin/bash

# SK Shieldus 41개 보안 진단 항목 테스트를 위한 취약한 AWS 환경 생성 스크립트
# AWS CloudShell에서 실행 가능
# 주의: 이 스크립트는 보안 테스트 목적으로만 사용하세요!

set -e

echo "==========================================="
echo "SK Shieldus 보안 진단 테스트 환경 생성"
echo "주의: 이 스크립트는 의도적으로 취약한 환경을 생성합니다!"
echo "테스트 완료 후 반드시 모든 리소스를 삭제하세요!"
echo "==========================================="

# 현재 리전과 계정 ID 가져오기
REGION=$(aws configure get region || echo "ap-northeast-2")
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TIMESTAMP=$(date +%Y%m%d%H%M%S)

echo "리전: $REGION"
echo "계정 ID: $ACCOUNT_ID"
echo "타임스탬프: $TIMESTAMP"

# ==========================================
# 1. 계정 관리 (1.1 ~ 1.13)
# ==========================================

echo -e "\n[1. 계정 관리 취약점 생성]"

# 1.1 사용자 계정 관리 - 테스트 계정 생성
echo "1.1 테스트 계정 생성..."
aws iam create-user --user-name test-vulnerable-user-$TIMESTAMP 2>/dev/null || true
aws iam create-user --user-name admin-test-$TIMESTAMP 2>/dev/null || true

# 1.2 IAM 단일 계정 관리 - 하나의 사용자에 여러 접근 키 생성
echo "1.2 다중 접근 키 생성..."
aws iam create-access-key --user-name test-vulnerable-user-$TIMESTAMP 2>/dev/null || true
aws iam create-access-key --user-name test-vulnerable-user-$TIMESTAMP 2>/dev/null || true

# 1.3 IAM 사용자 식별 - 태그 없는 사용자 생성
echo "1.3 태그 없는 사용자 생성..."
aws iam create-user --user-name notag-user-$TIMESTAMP 2>/dev/null || true

# 1.4 IAM 그룹 관리 - 그룹 없는 사용자에게 직접 정책 연결
echo "1.4 그룹 없이 직접 정책 연결..."
aws iam attach-user-policy --user-name test-vulnerable-user-$TIMESTAMP \
    --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess 2>/dev/null || true

# 1.5 EC2 키 페어 접근 관리 - 키 페어 없는 인스턴스 생성
echo "1.5 키 페어 생성 및 S3 업로드 준비..."
aws ec2 create-key-pair --key-name vulnerable-keypair-$TIMESTAMP \
    --query 'KeyMaterial' --output text > vulnerable-key-$TIMESTAMP.pem

# 1.6 S3 키 페어 저장 관리 - 키 페어를 S3에 저장
echo "1.6 S3 버킷 생성 및 키 페어 업로드..."
BUCKET_NAME="vulnerable-bucket-$ACCOUNT_ID-$TIMESTAMP"
aws s3 mb s3://$BUCKET_NAME --region $REGION 2>/dev/null || true
aws s3 cp vulnerable-key-$TIMESTAMP.pem s3://$BUCKET_NAME/ 2>/dev/null || true
rm -f vulnerable-key-$TIMESTAMP.pem

# 1.7 루트 계정 사용 - 시뮬레이션 (실제 루트 로그인은 불가)
echo "1.7 루트 계정 사용 시뮬레이션 (경고만 표시)..."

# 1.8 접근 키 관리 - 90일 이상 된 키 시뮬레이션
echo "1.8 오래된 접근 키 시뮬레이션..."

# 1.9 MFA 설정 - MFA 없는 사용자
echo "1.9 MFA 없는 사용자 생성 완료..."

# 1.10 패스워드 정책 - 약한 패스워드 정책
echo "1.10 약한 패스워드 정책 설정..."
aws iam update-account-password-policy \
    --minimum-password-length 6 \
    --no-require-symbols \
    --no-require-numbers \
    --no-require-uppercase-characters \
    --no-require-lowercase-characters \
    --allow-users-to-change-password \
    --no-password-reuse-prevention \
    --no-max-password-age 2>/dev/null || true

# ==========================================
# 2. 권한 관리 (2.1 ~ 2.3)
# ==========================================

echo -e "\n[2. 권한 관리 취약점 생성]"

# 2.1 인스턴스 서비스 정책 - 과도한 권한 역할
echo "2.1 과도한 권한의 EC2 역할 생성..."
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role --role-name vulnerable-ec2-role-$TIMESTAMP \
    --assume-role-policy-document file://trust-policy.json 2>/dev/null || true
aws iam attach-role-policy --role-name vulnerable-ec2-role-$TIMESTAMP \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true

# 2.2 네트워크 서비스 정책 - VPC 전체 권한
echo "2.2 과도한 네트워크 권한 정책 생성..."
cat > network-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "vpc:*"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy --policy-name vulnerable-network-policy-$TIMESTAMP \
    --policy-document file://network-policy.json 2>/dev/null || true

# 2.3 기타 서비스 정책 - 와일드카드 권한
echo "2.3 와일드카드 권한 정책 생성..."
cat > wildcard-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
EOF

aws iam create-policy --policy-name vulnerable-wildcard-policy-$TIMESTAMP \
    --policy-document file://wildcard-policy.json 2>/dev/null || true

# ==========================================
# 3. 가상 자원 (3.1 ~ 3.10)
# ==========================================

echo -e "\n[3. 가상 자원 취약점 생성]"

# VPC 및 서브넷 생성
echo "VPC 및 서브넷 생성..."
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
    --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=vulnerable-vpc-$TIMESTAMP}]" \
    --query 'Vpc.VpcId' --output text)

SUBNET_ID=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 \
    --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=vulnerable-subnet-$TIMESTAMP}]" \
    --query 'Subnet.SubnetId' --output text)

# 3.1 보안 그룹 ANY 설정
echo "3.1 0.0.0.0/0 허용 보안 그룹 생성..."
SG_ID=$(aws ec2 create-security-group --group-name vulnerable-sg-any-$TIMESTAMP \
    --description "Vulnerable security group with ANY rules" \
    --vpc-id $VPC_ID --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress --group-id $SG_ID \
    --protocol all --source 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-egress --group-id $SG_ID \
    --protocol all --destination 0.0.0.0/0 2>/dev/null || true

# 3.2 불필요한 포트 개방
echo "3.2 불필요한 포트 개방..."
SG_ID2=$(aws ec2 create-security-group --group-name vulnerable-sg-ports-$TIMESTAMP \
    --description "Security group with unnecessary ports" \
    --vpc-id $VPC_ID --query 'GroupId' --output text)

# Telnet, FTP, 불필요한 고위 포트 개방
aws ec2 authorize-security-group-ingress --group-id $SG_ID2 \
    --protocol tcp --port 23 --source 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID2 \
    --protocol tcp --port 21 --source 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID2 \
    --protocol tcp --port 135 --source 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID2 \
    --protocol tcp --port 445 --source 0.0.0.0/0 2>/dev/null || true

# 3.3 네트워크 ACL 모든 트래픽 허용
echo "3.3 모든 트래픽 허용 NACL 설정..."
NACL_ID=$(aws ec2 describe-network-acls --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'NetworkAcls[0].NetworkAclId' --output text)

aws ec2 create-network-acl-entry --network-acl-id $NACL_ID \
    --rule-number 100 --protocol all --rule-action allow \
    --ingress --cidr-block 0.0.0.0/0 2>/dev/null || true

# 3.4 라우팅 테이블 - 기본 라우트 0.0.0.0/0
echo "3.4 기본 라우트 설정..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=vulnerable-igw-$TIMESTAMP}]" \
    --query 'InternetGateway.InternetGatewayId' --output text)

aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID

RT_ID=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'RouteTables[0].RouteTableId' --output text)

aws ec2 create-route --route-table-id $RT_ID \
    --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID 2>/dev/null || true

# 3.5 인터넷 게이트웨이 연결
echo "3.5 모든 서브넷에 IGW 연결 완료..."

# 3.6 NAT 게이트웨이 (프라이빗 서브넷 없이)
echo "3.6 NAT 게이트웨이 설정 스킵 (비용 절감)..."

# 3.7 S3 버킷 퍼블릭 접근
echo "3.7 퍼블릭 S3 버킷 생성..."
cat > bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json 2>/dev/null || true
aws s3api put-public-access-block --bucket $BUCKET_NAME \
    --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" 2>/dev/null || true

# 3.8 RDS 서브넷 단일 AZ
echo "3.8 단일 AZ RDS 서브넷 그룹 생성..."
aws rds create-db-subnet-group --db-subnet-group-name vulnerable-db-subnet-$TIMESTAMP \
    --db-subnet-group-description "Single AZ subnet group" \
    --subnet-ids $SUBNET_ID 2>/dev/null || true

# 3.9, 3.10 EKS/ELB는 비용 문제로 스킵
echo "3.9 EKS Pod 보안 정책 - 스킵 (비용 절감)"
echo "3.10 ELB 제어 정책 - 스킵 (비용 절감)"

# ==========================================
# 4. 운영 관리 (4.1 ~ 4.15)
# ==========================================

echo -e "\n[4. 운영 관리 취약점 생성]"

# 4.1 EBS 암호화 미설정
echo "4.1 암호화되지 않은 EBS 볼륨 생성..."
# EC2 인스턴스 생성 시 암호화 안 된 볼륨 자동 생성

# 4.2 RDS 암호화 미설정
echo "4.2 암호화되지 않은 RDS 인스턴스 (스킵 - 비용)"

# 4.3 S3 암호화 미설정
echo "4.3 암호화되지 않은 S3 버킷..."
aws s3api put-bucket-encryption --bucket $BUCKET_NAME \
    --server-side-encryption-configuration '{"Rules":[]}' 2>/dev/null || true

# 4.4 통신구간 암호화 미설정
echo "4.4 HTTP 리스너 사용 (HTTPS 미사용)..."

# 4.5 CloudTrail 암호화 미설정
echo "4.5 암호화되지 않은 CloudTrail..."
aws cloudtrail create-trail --name vulnerable-trail-$TIMESTAMP \
    --s3-bucket-name $BUCKET_NAME --no-enable-log-file-validation 2>/dev/null || true

# 4.6 CloudWatch 암호화 미설정
echo "4.6 암호화되지 않은 CloudWatch 로그 그룹..."
aws logs create-log-group --log-group-name /aws/vulnerable-$TIMESTAMP 2>/dev/null || true

# 4.7 사용자 계정 접근 로깅 미설정
echo "4.7 CloudTrail 비활성화..."
aws cloudtrail stop-logging --name vulnerable-trail-$TIMESTAMP 2>/dev/null || true

# 4.8 인스턴스 로깅 미설정
echo "4.8 인스턴스 로깅 미설정 (인스턴스 생성 시 적용)..."

# 4.9 RDS 로깅 미설정
echo "4.9 RDS 로깅 미설정 (RDS 생성 시 적용)..."

# 4.10 S3 버킷 로깅 미설정
echo "4.10 S3 버킷 로깅 비활성화..."

# 4.11 VPC 플로우 로깅 미설정
echo "4.11 VPC 플로우 로그 비활성화..."

# 4.12 로그 보존 기간 미설정
echo "4.12 짧은 로그 보존 기간 설정..."
aws logs put-retention-policy --log-group-name /aws/vulnerable-$TIMESTAMP \
    --retention-in-days 1 2>/dev/null || true

# 4.13 백업 미사용
echo "4.13 백업 정책 미설정..."

# 4.14, 4.15 EKS 관련 스킵
echo "4.14 EKS 제어 플레인 로깅 - 스킵 (비용 절감)"
echo "4.15 EKS 클러스터 암호화 - 스킵 (비용 절감)"

# ==========================================
# EC2 인스턴스 생성 (여러 취약점 포함)
# ==========================================

echo -e "\n[취약한 EC2 인스턴스 생성]"

# 최신 Amazon Linux 2 AMI ID 가져오기
AMI_ID=$(aws ec2 describe-images --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)

# 인스턴스 프로파일 생성
aws iam create-instance-profile --instance-profile-name vulnerable-profile-$TIMESTAMP 2>/dev/null || true
aws iam add-role-to-instance-profile --instance-profile-name vulnerable-profile-$TIMESTAMP \
    --role-name vulnerable-ec2-role-$TIMESTAMP 2>/dev/null || true

# 잠시 대기 (IAM 반영 시간)
sleep 5

# EC2 인스턴스 생성
echo "취약한 설정의 EC2 인스턴스 생성..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t2.micro \
    --subnet-id $SUBNET_ID \
    --security-group-ids $SG_ID \
    --iam-instance-profile Name=vulnerable-profile-$TIMESTAMP \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=vulnerable-instance-$TIMESTAMP}]" \
    --no-associate-public-ip-address \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":8,"VolumeType":"gp2","DeleteOnTermination":true,"Encrypted":false}}]' \
    --query 'Instances[0].InstanceId' --output text 2>/dev/null) || echo "인스턴스 생성 실패"

# ==========================================
# 정리용 스크립트 생성
# ==========================================

echo -e "\n[정리 스크립트 생성]"
cat > cleanup-vulnerable-resources-$TIMESTAMP.sh <<EOF
#!/bin/bash
# 생성된 취약한 리소스들을 삭제하는 스크립트

echo "취약한 테스트 리소스 삭제 시작..."

# EC2 인스턴스 종료
aws ec2 terminate-instances --instance-ids $INSTANCE_ID 2>/dev/null || true
aws ec2 wait instance-terminated --instance-ids $INSTANCE_ID 2>/dev/null || true

# IAM 리소스 삭제
aws iam remove-role-from-instance-profile --instance-profile-name vulnerable-profile-$TIMESTAMP --role-name vulnerable-ec2-role-$TIMESTAMP 2>/dev/null || true
aws iam delete-instance-profile --instance-profile-name vulnerable-profile-$TIMESTAMP 2>/dev/null || true
aws iam detach-role-policy --role-name vulnerable-ec2-role-$TIMESTAMP --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true
aws iam delete-role --role-name vulnerable-ec2-role-$TIMESTAMP 2>/dev/null || true

# 사용자 정책 분리 및 삭제
aws iam detach-user-policy --user-name test-vulnerable-user-$TIMESTAMP --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess 2>/dev/null || true

# 접근 키 삭제
for key in \$(aws iam list-access-keys --user-name test-vulnerable-user-$TIMESTAMP --query 'AccessKeyMetadata[*].AccessKeyId' --output text 2>/dev/null); do
    aws iam delete-access-key --user-name test-vulnerable-user-$TIMESTAMP --access-key-id \$key 2>/dev/null || true
done

# 사용자 삭제
aws iam delete-user --user-name test-vulnerable-user-$TIMESTAMP 2>/dev/null || true
aws iam delete-user --user-name admin-test-$TIMESTAMP 2>/dev/null || true
aws iam delete-user --user-name notag-user-$TIMESTAMP 2>/dev/null || true

# 정책 삭제
POLICY_ARN1=\$(aws iam list-policies --query "Policies[?PolicyName=='vulnerable-network-policy-$TIMESTAMP'].Arn" --output text 2>/dev/null)
POLICY_ARN2=\$(aws iam list-policies --query "Policies[?PolicyName=='vulnerable-wildcard-policy-$TIMESTAMP'].Arn" --output text 2>/dev/null)
[ ! -z "\$POLICY_ARN1" ] && aws iam delete-policy --policy-arn \$POLICY_ARN1 2>/dev/null || true
[ ! -z "\$POLICY_ARN2" ] && aws iam delete-policy --policy-arn \$POLICY_ARN2 2>/dev/null || true

# S3 버킷 삭제
aws s3 rm s3://$BUCKET_NAME --recursive 2>/dev/null || true
aws s3api delete-bucket --bucket $BUCKET_NAME 2>/dev/null || true

# CloudTrail 삭제
aws cloudtrail delete-trail --name vulnerable-trail-$TIMESTAMP 2>/dev/null || true

# CloudWatch 로그 그룹 삭제
aws logs delete-log-group --log-group-name /aws/vulnerable-$TIMESTAMP 2>/dev/null || true

# 보안 그룹 삭제 (의존성 때문에 잠시 대기)
sleep 10
aws ec2 delete-security-group --group-id $SG_ID 2>/dev/null || true
aws ec2 delete-security-group --group-id $SG_ID2 2>/dev/null || true

# 네트워크 리소스 삭제
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID 2>/dev/null || true
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID 2>/dev/null || true
aws ec2 delete-subnet --subnet-id $SUBNET_ID 2>/dev/null || true
aws rds delete-db-subnet-group --db-subnet-group-name vulnerable-db-subnet-$TIMESTAMP 2>/dev/null || true
aws ec2 delete-vpc --vpc-id $VPC_ID 2>/dev/null || true

# 키 페어 삭제
aws ec2 delete-key-pair --key-name vulnerable-keypair-$TIMESTAMP 2>/dev/null || true

echo "취약한 테스트 리소스 삭제 완료!"
EOF

chmod +x cleanup-vulnerable-resources-$TIMESTAMP.sh

# ==========================================
# 완료 메시지
# ==========================================

echo -e "\n==========================================="
echo "취약한 테스트 환경 생성 완료!"
echo "==========================================="
echo "생성된 주요 리소스:"
echo "- VPC ID: $VPC_ID"
echo "- 보안 그룹 ID: $SG_ID, $SG_ID2"
echo "- S3 버킷: $BUCKET_NAME"
echo "- EC2 인스턴스 ID: $INSTANCE_ID"
echo ""
echo "테스트 완료 후 정리 방법:"
echo "./cleanup-vulnerable-resources-$TIMESTAMP.sh"
echo ""
echo "주의: 이 환경은 보안상 매우 취약합니다!"
echo "테스트 완료 후 반드시 모든 리소스를 삭제하세요!"
echo "==========================================="

# 임시 파일 정리
rm -f trust-policy.json network-policy.json wildcard-policy.json bucket-policy.json