# WALB 모니터링 API 명세서

## 기본 정보

-   **Base URL**: `/monitoring`
-   **인증**: 없음 (추후 구현 예정)
-   **응답 형식**: JSON

---

## 1. 모니터링 페이지

### GET `/monitoring/`

모니터링 메인 페이지를 반환합니다.

**Query Parameters:**

-   `account` (string, optional): 선택할 계정 ID

**응답:**

-   HTML 페이지

---

## 2. Kinesis 서비스 관리

### POST `/monitoring/kinesis/execute-script`

Kinesis 로그 수집 서비스 생성 스크립트를 실행합니다.

**Request Body:**

```
account_id=123456789012
```

**응답 예시:**

```json
{
    "success": true,
    "message": "Kinesis 서비스 스크립트 실행 완료",
    "script_command": "./create_kinesis_service.sh role 123456789012 arn:aws:iam::123456789012:role/WALB-Role ap-northeast-2",
    "actual_output": "실제 SSH 실행 결과...",
    "service_details": {
        "service_name": "kinesis-splunk-forwarder-123456789012",
        "service_file": "/etc/systemd/system/kinesis-splunk-forwarder-123456789012.service",
        "status": "active (running)"
    }
}
```

### GET `/monitoring/kinesis/service-status/{account_id}`

Kinesis 서비스 존재 여부 및 상태를 확인합니다.

**응답 예시:**

```json
{
    "success": true,
    "installation_complete": true,
    "service_name": "kinesis-splunk-forwarder-123456789012",
    "service_running": true,
    "service_enabled": true,
    "status_summary": "running",
    "log_files": {
        "cloudtrail": { "exists": true, "size_mb": 12.5 },
        "guardduty": { "exists": false },
        "security-hub": { "exists": false }
    }
}
```

### POST `/monitoring/kinesis/manage`

Kinesis 서비스를 시작/중지/재시작합니다.

**Request Body:**

```
account_id=123456789012
action=start|stop|restart
```

**응답 예시:**

```json
{
    "success": true,
    "message": "서비스가 성공적으로 시작되었습니다",
    "action": "start",
    "service_name": "kinesis-splunk-forwarder-123456789012"
}
```

### POST `/monitoring/kinesis/reinstall`

Kinesis 서비스를 완전히 재설치합니다 (기존 서비스 제거 후 설치).

**Request Body:**

```
account_id=123456789012
```

---

## 3. 로그 파일 모니터링

### GET `/monitoring/log-files/status/{account_id}`

실제 로그 파일 수집 상태를 확인합니다.

**응답 예시:**

```json
{
    "success": true,
    "account_id": "123456789012",
    "log_files": {
        "cloudtrail.log": {
            "exists": true,
            "size_mb": 45.2,
            "last_modified": "2024-01-10T15:30:00Z",
            "last_modified_ago": "5분 전",
            "is_recent": true
        },
        "guardduty.log": {
            "exists": false
        }
    },
    "overall_health": 66.7
}
```

### GET `/monitoring/log-files/preview/{account_id}/{log_type}`

특정 로그 파일의 최근 내용을 미리봅니다.

**Path Parameters:**

-   `log_type`: `cloudtrail`, `guardduty`, `security-hub` 중 하나

**응답 예시:**

```json
{
    "success": true,
    "file_exists": true,
    "file_size": 47316992,
    "total_lines": 1523,
    "last_modified": "2024-01-10T15:35:00Z",
    "formatted_content": "최근 50줄의 로그 내용..."
}
```

---

## 4. AWS 서비스 상태

### GET `/monitoring/aws/comprehensive-status/{account_id}`

AWS 서비스 종합 모니터링 상태를 조회합니다.

**응답 예시:**

```json
{
    "account_id": "123456789012",
    "account_name": "Production Account",
    "region": "ap-northeast-2",
    "overall_health": "healthy",
    "services": {
        "cloudwatch": {
            "active": true,
            "log_groups": [
                {
                    "name": "/aws/lambda/function1",
                    "size": 1048576,
                    "retention": 30
                }
            ],
            "total_size": 10485760
        },
        "cloudtrail": {
            "active": true,
            "total_trails": 2,
            "logging_enabled": 2,
            "trails": [...]
        },
        "guardduty": {
            "active": true,
            "detectors": [...],
            "finding_counts": {
                "High": 0,
                "Medium": 3,
                "Low": 12
            }
        }
    },
    "last_checked": "2024-01-10T15:40:00Z"
}
```

### GET `/monitoring/aws/service-details/{account_id}`

AWS 서비스 상태 상세 정보를 HTML 형태로 반환합니다.

**응답:**

-   HTML 페이지 (팝업 창에서 표시용)

---

## 5. 기존 서비스 관리 (레거시)

### POST `/monitoring/service/create`

Kinesis 서비스를 생성합니다 (시뮬레이션).

### POST `/monitoring/service/start`

Kinesis 서비스를 시작합니다 (시뮬레이션).

### POST `/monitoring/service/stop`

Kinesis 서비스를 중지합니다 (시뮬레이션).

### POST `/monitoring/service/remove`

Kinesis 서비스를 제거합니다 (시뮬레이션).

### GET `/monitoring/service/status/{account_id}`

서비스 상태를 조회합니다 (시뮬레이션).

### GET `/monitoring/service/logs/{account_id}`

서비스 로그를 조회합니다 (시뮬레이션).

---

## 6. Splunk 리다이렉션

### GET `/monitoring/splunk/redirect/{account_id}`

Splunk 대시보드로 리다이렉션합니다.

**Query Parameters:**

-   `log_type` (string): `cloudtrail`, `guardduty`, `security-hub`
-   `search` (string): 검색어
-   `time` (string): 시간 범위 (예: `-24h`)

**응답:**

-   302 Redirect to `http://3.39.158.137:8000/ko-KR/app/search/main_dashboard?tab=layout_1`

---

## 7. 유틸리티

### GET `/monitoring/kinesis/get-script-command/{account_id}`

계정별 스크립트 명령어를 조회합니다.

**응답 예시:**

```json
{
    "success": true,
    "script_command": "./create_kinesis_service.sh role 123456789012 arn:aws:iam::123456789012:role/WALB-Role ap-northeast-2",
    "full_command": "ssh -i splunk-ec2-key.pem ec2-user@192.168.1.100\n./create_kinesis_service.sh ...",
    "connection_type": "role"
}
```

### POST `/monitoring/ssh/service-status`

SSH를 통한 리눅스 서비스 상태를 확인합니다.

**Request Body:**

```
instance_ip=192.168.1.100
ssh_key_path=/opt/keys/splunk-ec2-key.pem
service_name=monitoring-service
```

---

## 에러 응답

모든 API는 실패 시 다음과 같은 형식으로 응답합니다:

```json
{
    "success": false,
    "message": "에러 메시지",
    "error": "상세 에러 내용 (선택적)"
}
```

**HTTP 상태 코드:**

-   `200`: 성공
-   `400`: 잘못된 요청
-   `404`: 리소스를 찾을 수 없음
-   `500`: 서버 내부 오류
