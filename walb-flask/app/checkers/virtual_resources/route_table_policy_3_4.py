"""
[3.4] 라우팅 테이블 정책 관리 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_4_route_table_policy.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class RouteTablePolicyChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.4"
    
    @property 
    def item_name(self):
        return "라우팅 테이블 정책 관리"
        
    def run_diagnosis(self):
        """
        [3.4] 라우팅 테이블 정책 관리
        - 서브넷이 퍼블릭이 아님에도 0.0.0.0/0 경로(ANY 정책)가 라우팅 테이블에 존재하는 경우 취약
        """
        print("[INFO] 3.4 라우팅 테이블 정책 관리 체크 중...")
        ec2 = self.session.client('ec2')
        misconfigured_routes = []

        try:
            # 1. 서브넷 정보 수집: 퍼블릭 IP 자동 할당 여부
            subnet_map = {
                s['SubnetId']: s.get('MapPublicIpOnLaunch', False)
                for s in ec2.describe_subnets()['Subnets']
            }

            # 2. 라우팅 테이블 반복
            for rt in ec2.describe_route_tables()['RouteTables']:
                rt_id = rt['RouteTableId']
                routes = rt.get('Routes', [])
                associations = rt.get('Associations', [])

                # 3. 0.0.0.0/0 대상 경로 추출
                any_route = next(
                    (r for r in routes if r.get('DestinationCidrBlock') == '0.0.0.0/0'),
                    None
                )

                if not any_route:
                    continue  # ANY 경로 없으면 다음 RT로

                # 4. 연결된 서브넷들 중 퍼블릭이 아닌 경우 취약으로 분류
                for assoc in associations:
                    subnet_id = assoc.get('SubnetId')
                    if not subnet_id:
                        continue  # main route table인 경우 무시

                    is_public = subnet_map.get(subnet_id, False)
                    if not is_public:
                        # 퍼블릭이 아닌데 ANY 경로 존재함 → 취약
                        target = any_route.get('GatewayId') or any_route.get('NatGatewayId') or "UnknownTarget"
                        misconfigured_routes.append({
                            "RouteTableId": rt_id,
                            "SubnetId": subnet_id,
                            "Target": target
                        })

            # 5. 결과 출력
            if not misconfigured_routes:
                print("[✓ COMPLIANT] 3.4 라우팅 테이블에 잘못된 ANY 정책이 발견되지 않았습니다.")
            else:
                print(f"[⚠ WARNING] 3.4 잘못된 ANY(0.0.0.0/0) 경로가 존재합니다 ({len(misconfigured_routes)}건).")
                for m in misconfigured_routes:
                    print(f"  ├─ 프라이빗 서브넷 '{m['SubnetId']}' → 라우팅 테이블 '{m['RouteTableId']}'에 ANY 경로 (→ {m['Target']}) 존재")

            has_issues = len(misconfigured_routes) > 0
            risk_level = self.calculate_risk_level(len(misconfigured_routes))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"잘못된 ANY 경로 {len(misconfigured_routes)}건 발견" if has_issues else "라우팅 테이블에 잘못된 ANY 정책이 발견되지 않았습니다",
                'misconfigured_routes': misconfigured_routes,
                'summary': f"총 {len(misconfigured_routes)}개의 잘못된 ANY 경로가 발견되었습니다." if has_issues else "모든 라우팅 테이블 정책이 안전합니다.",
                'details': {
                    'total_misconfigured_routes': len(misconfigured_routes),
                    'route_details': misconfigured_routes
                }
            }

        except ClientError as e:
            print(f"[ERROR] 정보 수집 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"정보 수집 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [3.4] 라우팅 테이블 정책 관리 조치
        - 자동 수정은 위험하므로 수동 가이드 제공
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('misconfigured_routes'):
            return {'status': 'no_action', 'message': '조치할 잘못된 라우팅이 없습니다.'}

        print("[FIX] 3.4 자동 조치는 지원하지 않습니다. 다음을 수동으로 조치하세요:")
        print("  └─ 1. 문제 서브넷의 라우팅 테이블에서 0.0.0.0/0 경로가 있는지 확인")
        print("  └─ 2. IGW 대신 NAT GW 또는 적절한 타깃으로 수정")
        print("  └─ 3. 필요 시 해당 서브넷을 퍼블릭 서브넷으로 전환하거나 라우팅 테이블 변경")

        return {
            'status': 'manual_required',
            'message': '자동 조치는 지원하지 않습니다. 수동 조치가 필요합니다.',
            'manual_guide': self._get_manual_guide()
        }

    def _get_manual_guide(self):
        """수동 조치 가이드 반환"""
        return {
            'title': '라우팅 테이블 정책 수동 조치 가이드',
            'description': '프라이빗 서브넷의 ANY 경로 설정을 수동으로 수정해야 합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 자동 수정 불가',
                    'content': '라우팅 테이블 수정은 네트워크 연결에 큰 영향을 미칠 수 있어 자동 조치를 지원하지 않습니다.'
                },
                {
                    'type': 'step',
                    'title': '1. 문제 상황 확인',
                    'content': '프라이빗 서브넷의 라우팅 테이블에 0.0.0.0/0 경로가 있는지 AWS 콘솔에서 확인하세요.'
                },
                {
                    'type': 'step',
                    'title': '2. 라우팅 테이블 수정',
                    'content': 'IGW(인터넷 게이트웨이) 대신 NAT Gateway 또는 적절한 타깃으로 수정하세요.'
                },
                {
                    'type': 'step',
                    'title': '3. 서브넷 설정 검토',
                    'content': '필요한 경우 해당 서브넷을 퍼블릭 서브넷으로 전환하거나 다른 라우팅 테이블을 연결하세요.'
                },
                {
                    'type': 'info',
                    'title': '[참고] 안전한 라우팅 설정',
                    'content': '프라이빗 서브넷은 NAT Gateway를 통해서만 외부 인터넷에 접근해야 합니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """수동 조치 옵션 반환"""
        if not diagnosis_result.get('misconfigured_routes'):
            return []
            
        misconfigured_routes = diagnosis_result['misconfigured_routes']
        
        return [{
            'id': 'manual_fix_routes',
            'title': '라우팅 테이블 수동 조치',
            'description': '잘못된 ANY 경로 설정을 수동으로 수정합니다. (자동 조치 불가)',
            'is_manual': True,
            'items': [
                {
                    'id': f"{route['RouteTableId']}_{route['SubnetId']}",
                    'name': f"서브넷 {route['SubnetId']}",
                    'description': f"라우팅 테이블 {route['RouteTableId']}의 ANY 경로 (타깃: {route['Target']})"
                }
                for route in misconfigured_routes
            ]
        }]