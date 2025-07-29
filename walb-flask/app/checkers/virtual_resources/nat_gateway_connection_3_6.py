"""
[3.6] NAT 게이트웨이 연결 관리 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_6_nat_gateway_connection.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class NatGatewayConnectionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.6"
    
    @property 
    def item_name(self):
        return "NAT 게이트웨이 연결 관리"
        
    def run_diagnosis(self):
        """
        [3.6] NAT 게이트웨이 연결 관리
        - NAT 게이트웨이의 연결 상태 출력
        - 라우팅 테이블에서 사용되지 않는 NAT 게이트웨이를 식별하여 리스트로 반환
        """
        print("[INFO] 3.6 NAT 게이트웨이 연결 현황 점검 중...")
        print("[ⓘ MANUAL] NAT 게이트웨이에 연결된 리소스가 외부 통신 필요 목적이 분명한지 판단할 수 없음")
        ec2 = self.session.client('ec2')
        unused_nat_ids = []
        nat_details = []

        try:
            # NAT 게이트웨이 조회
            nat_gateways = ec2.describe_nat_gateways(
                Filter=[{'Name': 'state', 'Values': ['pending', 'available']}]
            )['NatGateways']

            if not nat_gateways:
                print("[info] NAT 게이트웨이가 존재하지 않습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': 'NAT 게이트웨이가 존재하지 않습니다',
                    'unused_nat_ids': [],
                    'nat_details': [],
                    'summary': 'NAT 게이트웨이가 존재하지 않습니다.',
                    'details': {'total_nat_gateways': 0, 'unused_nat_gateways': 0}
                }

            # 라우팅 테이블 수집
            route_tables = ec2.describe_route_tables()['RouteTables']

            print("\n[NAT 게이트웨이 연결 현황]")
            for nat in nat_gateways:
                nat_id = nat['NatGatewayId']
                subnet_id = nat.get('SubnetId', 'Unknown')
                vpc_id = nat.get('VpcId', 'Unknown')
                state = nat['State']
                name_tag = next((tag['Value'] for tag in nat.get('Tags', []) if tag['Key'] == 'Name'), 'NoName')

                print(f"\n- NAT Gateway ID: {nat_id}")
                print(f"  이름: {name_tag}, 상태: {state}, VPC: {vpc_id}, Subnet: {subnet_id}")

                used = False
                used_by_routes = []
                for rt in route_tables:
                    for route in rt.get('Routes', []):
                        if route.get('NatGatewayId') == nat_id:
                            used = True
                            used_by_routes.append(rt['RouteTableId'])
                            print(f"  ⮡ 라우팅 테이블 '{rt['RouteTableId']}'에서 사용 중")
                            break

                nat_detail = {
                    'NatGatewayId': nat_id,
                    'Name': name_tag,
                    'State': state,
                    'VpcId': vpc_id,
                    'SubnetId': subnet_id,
                    'IsUsed': used,
                    'UsedByRoutes': used_by_routes
                }
                nat_details.append(nat_detail)

                if not used:
                    print("  ⚠️  사용되지 않음 (라우팅 테이블 연결 없음)")
                    unused_nat_ids.append(nat_id)

            if not unused_nat_ids:
                print("\n[✓ COMPLIANT] 모든 NAT 게이트웨이가 사용 중입니다.")
            else:
                print(f"\n[⚠ WARNING] 사용되지 않는 NAT 게이트웨이가 {len(unused_nat_ids)}개 존재합니다.")
                print("  ⮡ 대상:", ", ".join(unused_nat_ids))

            has_issues = len(unused_nat_ids) > 0
            risk_level = self.calculate_risk_level(len(unused_nat_ids))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"사용되지 않는 NAT 게이트웨이 {len(unused_nat_ids)}개 발견" if has_issues else "모든 NAT 게이트웨이가 사용 중입니다",
                'unused_nat_ids': unused_nat_ids,
                'nat_details': nat_details,
                'summary': f"총 {len(unused_nat_ids)}개의 미사용 NAT 게이트웨이가 발견되었습니다." if has_issues else "모든 NAT 게이트웨이가 사용 중입니다.",
                'details': {
                    'total_nat_gateways': len(nat_gateways),
                    'unused_nat_gateways': len(unused_nat_ids),
                    'nat_gateway_details': nat_details
                }
            }

        except ClientError as e:
            print(f"[ERROR] NAT 게이트웨이 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"NAT 게이트웨이 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [3.6] 미사용 NAT 게이트웨이에 대한 삭제 여부 확인 후 삭제
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('unused_nat_ids'):
            return {'status': 'no_action', 'message': '삭제할 NAT 게이트웨이가 없습니다.'}

        unused_nat_ids = diagnosis_result['unused_nat_ids']
        ec2 = self.session.client('ec2')
        results = []
        
        print("\n[FIX] 사용되지 않는 NAT 게이트웨이에 대한 조치를 시작합니다.")
        
        for nat_id in unused_nat_ids:
            # 선택된 항목인지 확인
            if any(nat_id in str(item) for item in selected_items.values() for item in item):
                try:
                    ec2.delete_nat_gateway(NatGatewayId=nat_id)
                    print(f"     [SUCCESS] NAT 게이트웨이 '{nat_id}' 삭제 요청 완료")
                    results.append({
                        'status': 'success',
                        'resource': f"NAT Gateway {nat_id}",
                        'action': f"NAT 게이트웨이 삭제",
                        'message': f"NAT 게이트웨이 '{nat_id}' 삭제 요청이 완료되었습니다."
                    })
                    
                except ClientError as e:
                    print(f"     [ERROR] 삭제 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': f"NAT Gateway {nat_id}",
                        'error': str(e),
                        'message': f"NAT 게이트웨이 '{nat_id}' 삭제 실패: {str(e)}"
                    })
            else:
                print(f"     [INFO] NAT 게이트웨이 '{nat_id}' 삭제를 건너뜁니다.")

        return {
            'status': 'success',
            'results': results,
            'message': f"{len(results)}개 항목에 대한 조치가 완료되었습니다."
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('unused_nat_ids'):
            return []
            
        unused_nat_ids = diagnosis_result['unused_nat_ids']
        nat_details = diagnosis_result.get('nat_details', [])
        
        # 미사용 NAT 게이트웨이 상세 정보 매칭
        unused_details = [detail for detail in nat_details if detail['NatGatewayId'] in unused_nat_ids]
        
        return [{
            'id': 'delete_unused_nat_gateways',
            'title': '미사용 NAT 게이트웨이 삭제',
            'description': '라우팅 테이블에서 사용되지 않는 NAT 게이트웨이를 삭제합니다. (삭제 전까지 비용 발생)',
            'items': [
                {
                    'id': detail['NatGatewayId'],
                    'name': f"NAT Gateway {detail['NatGatewayId']}",
                    'description': f"이름: {detail['Name']}, VPC: {detail['VpcId']} - 라우팅 테이블에서 미사용"
                }
                for detail in unused_details
            ]
        }]