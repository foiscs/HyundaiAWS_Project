"""
SK Shieldus 보안 진단 설정 및 데이터 관리
mainHub의 diagnosis_config.py를 Flask용으로 이식
"""

class DiagnosisConfig:
    """진단 설정 관리 클래스"""
    
    # 중요도별 색상 매핑
    SEVERITY_COLORS = {
        "상": "#e74c3c",  # 빨간색 - 높은 위험
        "중": "#f39c12",  # 주황색 - 중간 위험  
        "하": "#27ae60"   # 초록색 - 낮은 위험
    }
    
    # 위험도별 색상 매핑
    RISK_COLORS = {
        "high": "#e74c3c",     # 빨간색
        "medium": "#f39c12",   # 주황색
        "low": "#27ae60"       # 초록색
    }
    
    # 진단 상태별 색상
    STATUS_COLORS = {
        "idle": "#95a5a6",        # 회색 - 대기
        "running": "#3498db",     # 파란색 - 실행중
        "completed": "#27ae60",   # 초록색 - 완료
        "failed": "#e74c3c"       # 빨간색 - 실패
    }
    
    def get_sk_shieldus_items(self):
        """
        SK Shieldus 2024 기준 41개 보안 진단 항목 반환
        
        Returns:
            dict: 카테고리별 진단 항목 딕셔너리
        """
        return {
            "계정 관리": [
                {"code": "1.1", "name": "사용자 계정 관리", "severity": "상", "description": "관리자 계정과 테스트 계정을 점검합니다", "implemented": True},
                {"code": "1.2", "name": "IAM 단일 계정 관리", "severity": "상", "description": "IAM 사용자의 단일 계정 관리 상태를 점검합니다", "implemented": True},
                {"code": "1.3", "name": "IAM 사용자 식별", "severity": "중", "description": "IAM 사용자의 식별 및 인증 설정을 점검합니다", "implemented": True},
                {"code": "1.4", "name": "IAM 그룹 관리", "severity": "중", "description": "IAM 그룹의 권한 관리 상태를 점검합니다", "implemented": True},
                {"code": "1.5", "name": "EC2 키 페어 접근 관리", "severity": "상", "description": "EC2 인스턴스의 키 페어 접근 권한을 점검합니다", "implemented": True},
                {"code": "1.6", "name": "S3 키 페어 저장 관리", "severity": "상", "description": "S3에 저장된 키 페어의 보안을 점검합니다", "implemented": True},
                {"code": "1.7", "name": "사용자 접근 키 주기적 변경", "severity": "중", "description": "사용자 접근 키의 주기적 변경 상태를 점검합니다", "implemented": False},
                {"code": "1.8", "name": "접근 키 관리", "severity": "상", "description": "AWS 접근 키의 관리 상태를 점검합니다", "implemented": True},
                {"code": "1.9", "name": "MFA 설정", "severity": "상", "description": "다단계 인증(MFA) 설정 상태를 점검합니다", "implemented": True},
                {"code": "1.10", "name": "패스워드 정책", "severity": "중", "description": "계정 패스워드 정책 설정을 점검합니다", "implemented": True},
                {"code": "1.11", "name": "사용자 권한 검토", "severity": "중", "description": "사용자별 권한 할당 상태를 점검합니다", "implemented": False},
                {"code": "1.12", "name": "사용자 활동 모니터링", "severity": "중", "description": "사용자 활동 로그 및 모니터링을 점검합니다", "implemented": False},
                {"code": "1.13", "name": "계정 잠금 정책", "severity": "중", "description": "계정 잠금 및 해제 정책을 점검합니다", "implemented": False}
            ],
            "권한 관리": [
                {"code": "2.1", "name": "인스턴스 서비스 정책", "severity": "상", "description": "EC2 인스턴스의 서비스 정책을 점검합니다", "implemented": True},
                {"code": "2.2", "name": "네트워크 서비스 정책", "severity": "상", "description": "네트워크 관련 서비스 정책을 점검합니다", "implemented": True},
                {"code": "2.3", "name": "기타 서비스 정책", "severity": "중", "description": "기타 AWS 서비스의 정책을 점검합니다", "implemented": True}
            ],
            "가상 자원": [
                {"code": "3.1", "name": "보안그룹 ANY 설정", "severity": "상", "description": "보안그룹의 ANY(0.0.0.0/0) 설정을 점검합니다", "implemented": True},
                {"code": "3.2", "name": "보안그룹 불필요한 정책", "severity": "상", "description": "보안그룹의 불필요한 정책을 점검합니다", "implemented": True},
                {"code": "3.3", "name": "VPC 플로우 로그", "severity": "중", "description": "VPC 플로우 로그 설정을 점검합니다", "implemented": False},
                {"code": "3.4", "name": "ELB 접근 로그", "severity": "중", "description": "ELB의 접근 로그 설정을 점검합니다", "implemented": False},
                {"code": "3.5", "name": "CloudFront 로그", "severity": "중", "description": "CloudFront의 로그 설정을 점검합니다", "implemented": False},
                {"code": "3.6", "name": "NACL 설정", "severity": "중", "description": "네트워크 ACL의 설정을 점검합니다", "implemented": False},
                {"code": "3.7", "name": "Route Table 설정", "severity": "중", "description": "라우팅 테이블의 설정을 점검합니다", "implemented": False},
                {"code": "3.8", "name": "VPC 엔드포인트", "severity": "하", "description": "VPC 엔드포인트 설정을 점검합니다", "implemented": False},
                {"code": "3.9", "name": "인터넷 게이트웨이", "severity": "중", "description": "인터넷 게이트웨이 설정을 점검합니다", "implemented": False},
                {"code": "3.10", "name": "NAT 게이트웨이", "severity": "중", "description": "NAT 게이트웨이 설정을 점검합니다", "implemented": False}
            ],
            "운영 관리": [
                {"code": "4.1", "name": "EBS 암호화", "severity": "상", "description": "EBS 볼륨의 암호화 설정을 점검합니다", "implemented": False},
                {"code": "4.2", "name": "S3 암호화", "severity": "상", "description": "S3 버킷의 암호화 설정을 점검합니다", "implemented": False},
                {"code": "4.3", "name": "RDS 암호화", "severity": "상", "description": "RDS 인스턴스의 암호화 설정을 점검합니다", "implemented": False},
                {"code": "4.4", "name": "CloudTrail 설정", "severity": "상", "description": "CloudTrail의 로깅 설정을 점검합니다", "implemented": False},
                {"code": "4.5", "name": "CloudWatch 모니터링", "severity": "중", "description": "CloudWatch 모니터링 설정을 점검합니다", "implemented": False},
                {"code": "4.6", "name": "Config 설정", "severity": "중", "description": "AWS Config 설정을 점검합니다", "implemented": False},
                {"code": "4.7", "name": "GuardDuty 설정", "severity": "중", "description": "GuardDuty 위협 탐지 설정을 점검합니다", "implemented": False},
                {"code": "4.8", "name": "Trusted Advisor", "severity": "하", "description": "Trusted Advisor 권고사항을 점검합니다", "implemented": False},
                {"code": "4.9", "name": "KMS 키 관리", "severity": "상", "description": "KMS 키의 관리 상태를 점검합니다", "implemented": False},
                {"code": "4.10", "name": "Lambda 보안", "severity": "중", "description": "Lambda 함수의 보안 설정을 점검합니다", "implemented": False},
                {"code": "4.11", "name": "API Gateway 보안", "severity": "중", "description": "API Gateway의 보안 설정을 점검합니다", "implemented": False},
                {"code": "4.12", "name": "SNS 암호화", "severity": "중", "description": "SNS 토픽의 암호화 설정을 점검합니다", "implemented": False},
                {"code": "4.13", "name": "SQS 암호화", "severity": "중", "description": "SQS 큐의 암호화 설정을 점검합니다", "implemented": False},
                {"code": "4.14", "name": "ECR 이미지 스캔", "severity": "중", "description": "ECR 이미지의 보안 스캔을 점검합니다", "implemented": False},
                {"code": "4.15", "name": "EKS 보안", "severity": "상", "description": "EKS 클러스터의 보안 설정을 점검합니다", "implemented": False}
            ]
        }
    
    def get_item_by_code(self, item_code):
        """
        항목 코드로 특정 진단 항목 정보 반환
        
        Args:
            item_code (str): 진단 항목 코드 (예: "1.1")
            
        Returns:
            dict or None: 해당 항목 정보 또는 None
        """
        items = self.get_sk_shieldus_items()
        
        for category, category_items in items.items():
            for item in category_items:
                if item["code"] == item_code:
                    item["category"] = category
                    return item
        
        return None
    
    def get_items_by_category(self, category):
        """
        카테고리별 진단 항목 목록 반환
        
        Args:
            category (str): 카테고리명
            
        Returns:
            list: 해당 카테고리의 진단 항목 목록
        """
        items = self.get_sk_shieldus_items()
        return items.get(category, [])
    
    def get_items_by_severity(self, severity):
        """
        중요도별 진단 항목 목록 반환
        
        Args:
            severity (str): 중요도 ("상", "중", "하")
            
        Returns:
            list: 해당 중요도의 진단 항목 목록
        """
        items = self.get_sk_shieldus_items()
        result = []
        
        for category, category_items in items.items():
            for item in category_items:
                if item["severity"] == severity:
                    item["category"] = category
                    result.append(item)
        
        return result
    
    def get_total_items_count(self):
        """
        전체 진단 항목 수 반환
        
        Returns:
            int: 전체 항목 수
        """
        items = self.get_sk_shieldus_items()
        total = 0
        
        for category_items in items.values():
            total += len(category_items)
        
        return total
    
    def get_severity_stats(self):
        """
        중요도별 항목 수 통계 반환
        
        Returns:
            dict: 중요도별 항목 수
        """
        items = self.get_sk_shieldus_items()
        stats = {"상": 0, "중": 0, "하": 0}
        
        for category_items in items.values():
            for item in category_items:
                severity = item["severity"]
                if severity in stats:
                    stats[severity] += 1
        
        return stats
    
    def get_category_stats(self):
        """
        카테고리별 항목 수 통계 반환
        
        Returns:
            dict: 카테고리별 항목 수
        """
        items = self.get_sk_shieldus_items()
        stats = {}
        
        for category, category_items in items.items():
            stats[category] = len(category_items)
        
        return stats
    
    def get_color_by_severity(self, severity):
        """
        중요도에 따른 색상 반환
        
        Args:
            severity (str): 중요도
            
        Returns:
            str: CSS 색상 코드
        """
        return self.SEVERITY_COLORS.get(severity, "#95a5a6")
    
    def get_color_by_risk(self, risk_level):
        """
        위험도에 따른 색상 반환
        
        Args:
            risk_level (str): 위험도
            
        Returns:
            str: CSS 색상 코드
        """
        return self.RISK_COLORS.get(risk_level, "#95a5a6")
    
    def get_color_by_status(self, status):
        """
        상태에 따른 색상 반환
        
        Args:
            status (str): 진단 상태
            
        Returns:
            str: CSS 색상 코드
        """
        return self.STATUS_COLORS.get(status, "#95a5a6")

# 전역 함수들 (mainHub 호환성을 위해)
def get_sk_shieldus_items():
    """SK Shieldus 진단 항목 반환 (전역 함수)"""
    config = DiagnosisConfig()
    return config.get_sk_shieldus_items()

def get_severity_color(severity):
    """중요도별 색상 반환 (전역 함수)"""
    config = DiagnosisConfig()
    return config.get_color_by_severity(severity)

def get_risk_color(risk_level):
    """위험도별 색상 반환 (전역 함수)"""
    config = DiagnosisConfig()
    return config.get_color_by_risk(risk_level)