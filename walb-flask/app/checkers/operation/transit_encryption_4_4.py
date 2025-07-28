"""
[4.4] 통신구간 암호화 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_4_transit_encryption.py
"""

from app.checkers.base_checker import BaseChecker


class TransitEncryptionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.4"
    
    @property 
    def item_name(self):
        return "통신구간 암호화 설정"
        
    def run_diagnosis(self):
        """
        [4.4] 통신구간 암호화 설정 (수동 점검 안내)
        """
        print("[INFO] 4.4 통신구간 암호화 설정 체크 중...")
        print("[ⓘ MANUAL] 통신구간 암호화는 서비스 구성에 따라 달라지므로 자동 점검이 제한됩니다.")
        print("  ├─ 점검 1: [3.10 ELB 연결 관리] 항목을 통해 로드 밸런서의 HTTPS/TLS 리스너 및 리디렉션 설정을 확인하세요.")
        print("  ├─ 점검 2: CloudFront 배포가 있다면, Viewer Protocol Policy가 'Redirect HTTP to HTTPS' 또는 'HTTPS Only'인지 확인하세요.")
        print("  └─ 점검 3: 애플리케이션 간 직접 통신 시 TLS가 적용되었는지 코드 및 구성 레벨에서 확인하세요.")

        # 수동 점검이 필요하므로 항상 has_issues = True
        has_issues = True
        risk_level = 'medium'  # 수동 점검 필요한 항목은 중간 위험도
        
        return {
            'status': 'success',
            'has_issues': has_issues,
            'risk_level': risk_level,
            'message': '통신구간 암호화는 수동 점검이 필요합니다',
            'manual_check_required': True,
            'summary': '통신구간 암호화 설정에 대한 수동 점검이 필요합니다.',
            'details': {
                'requires_manual_check': True,
                'check_points': [
                    'ELB/ALB HTTPS/TLS 리스너 및 리디렉션 설정',
                    'CloudFront Viewer Protocol Policy 설정', 
                    '애플리케이션 간 직접 통신 TLS 적용'
                ]
            }
        }

    def execute_fix(self, selected_items):
        """
        [4.4] 통신구간 암호화 설정 조치 (수동 조치 안내)
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        print("[FIX] 4.4 통신구간 암호화 조치 가이드입니다.")
        print("  └─ [ELB/ALB] 3.10 항목의 fix 가이드를 참고하여 HTTP 리스너를 HTTPS로 리디렉션하도록 수정하세요.")
        print("  └─ [CloudFront] 배포판의 [Behaviors] 탭에서 'Viewer Protocol Policy'를 'Redirect HTTP to HTTPS'로 변경하세요.")
        print("  └─ [애플리케이션] 내부 통신에 mTLS(상호 TLS)를 적용하거나, 서비스 메쉬(예: Istio, App Mesh)를 사용하여 통신 암호화를 강제하는 것을 고려하세요.")

        return {
            'status': 'manual_required',
            'message': '통신구간 암호화 설정은 수동 조치가 필요합니다.',
            'manual_guide': self._get_manual_guide()
        }

    def _get_manual_guide(self):
        """수동 조치 가이드 반환"""
        return {
            'title': '통신구간 암호화 수동 점검 및 조치 가이드',
            'description': '통신구간 암호화는 서비스 구성에 따라 달라지므로 각 구성 요소별로 수동 점검이 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 수동 점검 필요',
                    'content': '통신구간 암호화는 애플리케이션 아키텍처에 따라 설정이 달라 자동 점검이 제한됩니다.'
                },
                {
                    'type': 'step',
                    'title': '1. ELB/ALB HTTPS 설정 점검',
                    'content': '[3.10 ELB 연결 관리] 항목을 통해 로드 밸런서의 HTTPS/TLS 리스너 및 HTTP → HTTPS 리디렉션 설정을 확인하세요.'
                },
                {
                    'type': 'step',
                    'title': '2. CloudFront 암호화 정책 점검',
                    'content': 'CloudFront 배포가 있다면 Viewer Protocol Policy가 "Redirect HTTP to HTTPS" 또는 "HTTPS Only"인지 확인하세요.'
                },
                {
                    'type': 'step',
                    'title': '3. 애플리케이션 간 통신 암호화 점검',
                    'content': '마이크로서비스나 애플리케이션 간 직접 통신 시 TLS가 적용되었는지 코드 및 구성 레벨에서 확인하세요.'
                },
                {
                    'type': 'step',
                    'title': '4. ELB/ALB HTTPS 리디렉션 설정',
                    'content': 'HTTP 리스너를 HTTPS로 리디렉션하도록 수정하여 모든 트래픽이 암호화되도록 설정하세요.'
                },
                {
                    'type': 'step',
                    'title': '5. CloudFront 보안 정책 적용',
                    'content': 'CloudFront 배포의 Behaviors 탭에서 Viewer Protocol Policy를 "Redirect HTTP to HTTPS"로 변경하세요.'
                },
                {
                    'type': 'step',
                    'title': '6. 서비스 메쉬 고려',
                    'content': '내부 통신에 mTLS(상호 TLS)를 적용하거나 서비스 메쉬(Istio, App Mesh)를 사용하여 통신 암호화를 강제하는 것을 고려하세요.'
                },
                {
                    'type': 'info',
                    'title': '[참고] 통신 암호화 모범 사례',
                    'content': '모든 외부 통신은 HTTPS/TLS 사용, 내부 통신도 가능한 한 암호화하여 보안을 강화하세요.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """수동 조치 옵션 반환"""
        return [{
            'id': 'manual_transit_encryption_check',
            'title': '통신구간 암호화 수동 점검',
            'description': '통신구간 암호화 설정을 수동으로 점검하고 조치합니다.',
            'is_manual': True,
            'items': [
                {
                    'id': 'elb_https_check',
                    'name': 'ELB/ALB HTTPS 설정',
                    'description': 'HTTP 리스너 HTTPS 리디렉션 및 TLS 리스너 점검'
                },
                {
                    'id': 'cloudfront_policy_check',
                    'name': 'CloudFront 정책 점검',
                    'description': 'Viewer Protocol Policy HTTPS 강제 설정 점검'
                },
                {
                    'id': 'application_tls_check',
                    'name': '애플리케이션 통신 암호화',
                    'description': '마이크로서비스 간 TLS 통신 설정 점검'
                }
            ]
        }]