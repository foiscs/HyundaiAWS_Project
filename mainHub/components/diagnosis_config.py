"""
WALB 진단 데이터 및 상수 정의 모듈
SK Shieldus 41개 보안 진단 항목과 관련 상수들을 중앙 관리

Functions:
- DiagnosisDataConfig: 진단 설정 클래스
- get_sk_shieldus_items: SK Shieldus 41개 진단 항목 반환
- IMPORTANCE_COLORS: 중요도별 색상 매핑
- RISK_COLORS: 위험도별 색상 매핑
"""

from typing import Dict, List

def get_sk_shieldus_items():
    """SK Shieldus 41개 진단 항목 반환"""
    return {
        "계정 관리": [
            {"code": "1.1", "name": "사용자 계정 관리", "importance": "상", "description": "AWS 계정의 IAM 사용자들이 적절한 권한과 정책으로 관리되고 있는지, 불필요한 권한이 부여되지 않았는지를 진단합니다."},
            {"code": "1.2", "name": "IAM 사용자 계정 단일화 관리", "importance": "상", "description": "한 명의 사용자가 여러 개의 IAM 계정을 보유하고 있지 않은지, 1인 1계정 원칙이 준수되고 있는지를 점검합니다."},
            {"code": "1.3", "name": "IAM 사용자 계정 식별 관리", "importance": "중", "description": "모든 IAM 사용자에게 이름, 부서, 역할 등의 식별 태그가 적절히 설정되어 있어 사용자를 명확히 구분할 수 있는지 진단합니다."},
            {"code": "1.4", "name": "IAM 그룹 사용자 계정 관리", "importance": "중", "description": "IAM 사용자들이 개별 권한 대신 그룹 기반으로 권한을 관리받고 있는지, 그룹별 권한이 적절히 분리되어 있는지를 점검합니다."},
            {"code": "1.5", "name": "Key Pair 접근 관리", "importance": "상", "description": "실행 중인 모든 EC2 인스턴스에 Key Pair가 할당되어 패스워드 없이 안전한 SSH 접근이 가능한지를 진단합니다."},
            {"code": "1.6", "name": "Key Pair 보관 관리", "importance": "상", "description": "EC2 Key Pair 파일(.pem)이 공개 접근 가능한 S3 버킷에 저장되어 보안 위험을 초래하지 않는지 점검합니다."},
            {"code": "1.7", "name": "Admin Console 관리자 정책 관리", "importance": "중", "description": "AWS Management Console의 관리자 권한이 필요 이상으로 부여되지 않았는지, 관리자 계정 사용이 적절한지를 진단합니다."},
            {"code": "1.8", "name": "Admin Console 계정 Access Key 활성화 및 사용주기 관리", "importance": "상", "description": "관리자 계정의 Access Key가 장기간 사용되고 있지 않은지, 정기적인 로테이션이 이루어지고 있는지를 점검합니다."},
            {"code": "1.9", "name": "MFA (Multi-Factor Authentication) 설정", "importance": "중", "description": "중요한 IAM 사용자와 루트 계정에 다중 인증(MFA)이 활성화되어 계정 보안이 강화되어 있는지 진단합니다."},
            {"code": "1.10", "name": "AWS 계정 패스워드 정책 관리", "importance": "중", "description": "IAM 계정의 패스워드 정책이 충분히 강력하게 설정되어 있는지, 길이/복잡도/만료 정책이 적절한지를 점검합니다."},
            {"code": "1.11", "name": "EKS 사용자 관리", "importance": "상", "description": "Amazon EKS 클러스터에 접근하는 사용자들의 권한이 적절히 관리되고 있는지, 불필요한 클러스터 접근 권한이 없는지 진단합니다."},
            {"code": "1.12", "name": "EKS 서비스 어카운트 관리", "importance": "중", "description": "EKS 클러스터 내 Kubernetes 서비스 어카운트들이 최소 권한 원칙에 따라 관리되고 있는지를 점검합니다."},
            {"code": "1.13", "name": "EKS 불필요한 익명 접근 관리", "importance": "상", "description": "EKS 클러스터에 익명 사용자의 접근이 허용되어 있지 않은지, 인증되지 않은 접근 경로가 차단되어 있는지 진단합니다."}
        ],
        "권한 관리": [
            {"code": "2.1", "name": "인스턴스 서비스 정책 관리", "importance": "상", "description": "EC2, RDS, S3 등 핵심 AWS 서비스에 대한 IAM 정책이 과도한 권한을 부여하지 않고 최소 권한 원칙을 준수하는지 진단합니다."},
            {"code": "2.2", "name": "네트워크 서비스 정책 관리", "importance": "상", "description": "VPC, Route53, CloudFront 등 네트워크 관련 서비스의 IAM 권한이 적절히 제한되어 있는지, 네트워크 설정 변경 권한이 안전하게 관리되는지 점검합니다."},
            {"code": "2.3", "name": "기타 서비스 정책 관리", "importance": "상", "description": "CloudWatch, CloudTrail, Lambda 등 기타 AWS 서비스들에 대한 권한이 업무 목적에 맞게 최소한으로 부여되어 있는지 진단합니다."}
        ],
        "가상 리소스 관리": [
            {"code": "3.1", "name": "보안 그룹 인/아웃바운드 ANY 설정 관리", "importance": "상", "description": "EC2 보안 그룹에서 모든 포트(0-65535)를 허용하는 위험한 ANY 설정이 사용되고 있지 않은지 점검합니다."},
            {"code": "3.2", "name": "보안 그룹 인/아웃바운드 불필요 정책 관리", "importance": "상", "description": "사용되지 않는 보안 그룹이나 ANY IP(0.0.0.0/0) 규칙을 포함한 불필요한 보안 그룹이 있는지 찾아 정리가 필요한지 진단합니다."},
            {"code": "3.3", "name": "네트워크 ACL 인/아웃바운드 트래픽 정책 관리", "importance": "중", "description": "VPC의 Network ACL에서 과도하게 개방된 트래픽 규칙이 있는지, 필요한 트래픽만 허용하도록 설정되어 있는지 점검합니다."},
            {"code": "3.4", "name": "라우팅 테이블 정책 관리", "importance": "중", "description": "VPC 라우팅 테이블에서 불필요한 라우팅 경로나 보안상 위험한 라우팅 설정이 있는지, 프라이빗 서브넷의 격리가 적절한지 진단합니다."},
            {"code": "3.5", "name": "인터넷 게이트웨이 연결 관리", "importance": "하", "description": "인터넷 게이트웨이가 필요하지 않은 VPC나 서브넷에 연결되어 있지 않은지, IGW 연결 상태가 보안 정책에 부합하는지 점검합니다."},
            {"code": "3.6", "name": "NAT 게이트웨이 연결 관리", "importance": "중", "description": "프라이빗 서브넷의 아웃바운드 인터넷 접근을 위한 NAT Gateway 설정이 적절한지, 불필요한 NAT 연결이 없는지 진단합니다."},
            {"code": "3.7", "name": "S3 버킷/객체 접근 관리", "importance": "중", "description": "S3 버킷이 의도치 않게 퍼블릭으로 노출되어 있지 않은지, 버킷 정책과 ACL이 적절히 설정되어 데이터가 안전한지 점검합니다."},
            {"code": "3.8", "name": "RDS 서브넷 가용 영역 관리", "importance": "중", "description": "RDS 인스턴스가 적절한 서브넷 그룹에 배치되어 있는지, 다중 AZ 구성으로 고가용성이 확보되어 있는지 진단합니다."},
            {"code": "3.9", "name": "EKS Pod 보안 정책 관리", "importance": "상", "description": "EKS 클러스터에서 Pod Security Standards가 적용되어 있는지, 컨테이너 실행 권한이 적절히 제한되어 있는지 점검합니다."},
            {"code": "3.10", "name": "ELB(Elastic Load Balancing) 연결 관리", "importance": "중", "description": "로드밸런서의 리스너 설정과 보안 그룹이 적절한지, SSL/TLS 설정이 안전하게 구성되어 있는지 진단합니다."}
        ],
        "운영 관리": [
            {"code": "4.1", "name": "EBS 및 볼륨 암호화 설정", "importance": "중", "description": "EC2 인스턴스의 EBS 볼륨과 스냅샷이 암호화되어 저장되고 있는지, 데이터 유출 시 보호가 가능한지 점검합니다."},
            {"code": "4.2", "name": "RDS 암호화 설정", "importance": "중", "description": "RDS 데이터베이스 인스턴스의 저장 데이터와 백업이 암호화되어 있는지, 전송 중 암호화도 적용되어 있는지 진단합니다."},
            {"code": "4.3", "name": "S3 암호화 설정", "importance": "중", "description": "S3 버킷에 기본 암호화가 활성화되어 있는지, 업로드되는 모든 객체가 자동으로 암호화되도록 설정되어 있는지 점검합니다."},
            {"code": "4.4", "name": "통신구간 암호화 설정", "importance": "중", "description": "AWS 서비스 간 통신과 클라이언트-서버 간 데이터 전송이 TLS/SSL로 암호화되어 있는지, HTTPS 사용이 강제되는지 진단합니다."},
            {"code": "4.5", "name": "CloudTrail 암호화 설정", "importance": "중", "description": "AWS CloudTrail 로그가 KMS 키로 암호화되어 저장되고 있는지, 감사 로그의 무결성이 보장되는지 점검합니다."},
            {"code": "4.6", "name": "CloudWatch 암호화 설정", "importance": "중", "description": "CloudWatch 로그 그룹이 KMS 암호화로 보호되고 있는지, 모니터링 데이터가 안전하게 저장되는지 진단합니다."},
            {"code": "4.7", "name": "AWS 사용자 계정 로깅 설정", "importance": "상", "description": "IAM 사용자들의 모든 활동이 CloudTrail을 통해 기록되고 있는지, 계정 사용 내역을 추적할 수 있는지 점검합니다."},
            {"code": "4.8", "name": "인스턴스 로깅 설정", "importance": "중", "description": "EC2 인스턴스의 시스템 로그와 애플리케이션 로그가 CloudWatch나 중앙 로깅 시스템으로 수집되고 있는지 진단합니다."},
            {"code": "4.9", "name": "RDS 로깅 설정", "importance": "중", "description": "RDS 데이터베이스의 쿼리 로그, 에러 로그, 슬로우 쿼리 로그가 활성화되어 데이터베이스 활동을 모니터링할 수 있는지 점검합니다."},
            {"code": "4.10", "name": "S3 버킷 로깅 설정", "importance": "중", "description": "S3 버킷에 액세스 로깅이 활성화되어 있는지, 버킷에 대한 모든 요청이 기록되어 추적 가능한지 진단합니다."},
            {"code": "4.11", "name": "VPC 플로우 로깅 설정", "importance": "중", "description": "VPC Flow Logs가 활성화되어 네트워크 트래픽이 기록되고 있는지, 네트워크 보안 분석이 가능한지 점검합니다."},
            {"code": "4.12", "name": "로그 보관 기간 설정", "importance": "중", "description": "각종 로그들의 보존 기간이 규정에 맞게 설정되어 있는지, 비용 효율적이면서도 규정을 준수하는지 진단합니다."},
            {"code": "4.13", "name": "백업 사용 여부", "importance": "중", "description": "중요한 데이터와 시스템에 대한 백업 정책이 수립되어 있는지, 자동 백업이 정상적으로 수행되고 있는지 점검합니다."},
            {"code": "4.14", "name": "EKS Cluster 제어 플레인 로깅 설정", "importance": "중", "description": "EKS 클러스터의 API 서버, 감사, 인증 등 제어 플레인 로그가 CloudWatch로 전송되어 기록되고 있는지 진단합니다."},
            {"code": "4.15", "name": "EKS Cluster 암호화 설정", "importance": "중", "description": "EKS 클러스터의 etcd에 저장되는 Kubernetes Secret이 KMS 키로 암호화되어 있는지, 클러스터 데이터가 안전한지 점검합니다."}
        ]
    }

# 중요도별 색상 매핑
IMPORTANCE_COLORS = {
    "상": "🔴",
    "중": "🟡", 
    "하": "🟢"
}

# 위험도별 색상 매핑  
RISK_COLORS = {
    "high": ("🔴", "#e53e3e", "높음"),
    "medium": ("🟡", "#dd6b20", "보통"), 
    "low": ("🟢", "#38a169", "낮음")
}

class DiagnosisDataConfig:
    """진단 설정 클래스 - 모든 상수와 설정 중앙화"""
    
    def get_diagnosis_items(self) -> Dict[str, List[Dict]]:
        """진단 항목 반환"""
        return get_sk_shieldus_items()
    
    def get_importance_colors(self) -> Dict[str, str]:
        """중요도 색상 반환"""
        return IMPORTANCE_COLORS
    
    def get_risk_colors(self) -> Dict[str, tuple]:
        """위험도 색상 반환"""
        return RISK_COLORS
    
    def get_total_items_count(self) -> int:
        """총 진단 항목 수 반환"""
        items = self.get_diagnosis_items()
        return sum(len(items_list) for items_list in items.values())
    
    def get_items_by_risk_level(self) -> Dict[str, int]:
        """위험도별 항목 수 반환"""
        items = self.get_diagnosis_items()
        risk_counts = {"상": 0, "중": 0, "하": 0}
        
        for category_items in items.values():
            for item in category_items:
                importance = item.get("importance", "중")
                if importance in risk_counts:
                    risk_counts[importance] += 1
        
        return risk_counts

