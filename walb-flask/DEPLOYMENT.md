# WALB Flask 운영 환경 배포 가이드

## 1. SSH 접속 설정

### 환경 변수 설정

운영 환경에서는 `.env` 파일을 생성하여 SSH 접속 정보를 설정합니다.

```bash
# .env 파일 생성
cp .env.example .env

# 실제 운영 환경 값으로 수정
vim .env
```

### 환경 변수 설명

```bash
# Splunk EC2 인스턴스 Private IP (VPC 내부 접근)
SSH_INSTANCE_IP=192.168.1.100

# SSH 키 파일 경로 (서버 내 절대 경로)
SSH_KEY_PATH=/opt/keys/splunk-ec2-key.pem

# SSH 사용자명
SSH_USER=ec2-user

# SSH 키 파일명 (표시용)
SSH_KEY_NAME=splunk-ec2-key.pem
```

## 2. SSH 키 파일 설정

### 키 파일 배치

```bash
# 키 디렉토리 생성
sudo mkdir -p /opt/keys

# 키 파일 복사 (실제 키 파일로 교체)
sudo cp splunk-ec2-key.pem /opt/keys/

# 권한 설정
sudo chmod 600 /opt/keys/splunk-ec2-key.pem
sudo chown www-data:www-data /opt/keys/splunk-ec2-key.pem
```

### 보안 고려사항

1. **SSH 키 파일은 반드시 Git에 포함하지 않음**
2. **키 파일 권한은 600 (소유자만 읽기/쓰기)**
3. **웹 서버가 키 파일에 접근 가능하도록 소유권 설정**

## 3. 네트워크 접근 설정

### VPC 내부 접근

운영 환경에서는 Private IP를 사용하므로 다음을 확인:

1. **웹 서버와 Splunk EC2가 같은 VPC에 위치**
2. **Security Group에서 SSH(22) 포트 허용**
3. **NACL에서 SSH 트래픽 허용**

### 로컬 테스트 vs 운영 환경

```python
# 로컬 테스트 (이전 설정)
SSH_INSTANCE_IP=3.35.197.218        # Public IP
SSH_KEY_PATH=C:\Users\User\SplunkEc2.pem

# 운영 환경 (현재 설정)
SSH_INSTANCE_IP=192.168.1.100       # Private IP
SSH_KEY_PATH=/opt/keys/splunk-ec2-key.pem
```

## 4. 배포 절차

### 4.1 의존성 설치

```bash
# 가상환경 활성화
source venv/bin/activate

# 새로운 의존성 설치
pip install -r requirements.txt
```

### 4.2 환경 설정

```bash
# .env 파일 설정
cp .env.example .env
vim .env

# SSH 키 파일 배치
sudo cp your-ssh-key.pem /opt/keys/splunk-ec2-key.pem
sudo chmod 600 /opt/keys/splunk-ec2-key.pem
sudo chown www-data:www-data /opt/keys/splunk-ec2-key.pem
```

### 4.3 애플리케이션 재시작

```bash
# Gunicorn 재시작
sudo systemctl restart walb-flask

# 또는 pm2 사용 시
pm2 restart walb-flask
```

## 5. 검증

### SSH 접속 테스트

```bash
# 수동으로 SSH 접속 테스트
ssh -i /opt/keys/splunk-ec2-key.pem ec2-user@192.168.1.100

# 키 권한 확인
ls -la /opt/keys/splunk-ec2-key.pem
```

### 웹 인터페이스 테스트

1. **모니터링 페이지 접속**
2. **계정 선택 후 Kinesis 서비스 생성 테스트**
3. **로그 파일 상태 확인 테스트**
4. **서비스 시작/중지/재시작 테스트**

## 6. 문제 해결

### SSH 접속 실패

```bash
# SSH 키 권한 확인
ls -la /opt/keys/splunk-ec2-key.pem

# 네트워크 연결 테스트
ping 192.168.1.100
telnet 192.168.1.100 22

# SSH 디버그 모드
ssh -vvv -i /opt/keys/splunk-ec2-key.pem ec2-user@192.168.1.100
```

### 환경 변수 로드 실패

```bash
# .env 파일 존재 확인
ls -la .env

# python-dotenv 설치 확인
pip list | grep python-dotenv

# Flask 로그 확인
tail -f /var/log/walb-flask/app.log
```

## 7. 로그 모니터링

### 애플리케이션 로그

```bash
# Flask 애플리케이션 로그
tail -f /var/log/walb-flask/app.log

# SSH 실행 로그 (MonitoringService)
grep -i ssh /var/log/walb-flask/app.log

# 에러 로그
grep -i error /var/log/walb-flask/app.log
```

### 시스템 로그

```bash
# SSH 연결 로그
sudo tail -f /var/log/auth.log

# 시스템 서비스 로그
sudo journalctl -u walb-flask -f
```