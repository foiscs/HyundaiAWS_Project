"""
[3.5] 인터넷 게이트웨이 연결 관리 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_5_igw_connection.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class InternetGatewayConnectionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.5"
    
    @property 
    def item_name(self):
        return "인터넷 게이트웨이 연결 관리"
        
    def run_diagnosis(self):
        """
        [3.5] 인터넷 게이트웨이 연결 관리  
        - 어떤 VPC에도 연결되지 않은 'detached' 상태의 인터넷 게이트웨이를 점검하고, 해당 ID 및 이름 목록 반환
        """
        print("[INFO] 3.5 인터넷 게이트웨이 연결 관리 체크 중...")
        ec2 = self.session.client('ec2')
        detached_igws = []

        try:
            for igw in ec2.describe_internet_gateways()['InternetGateways']:
                # Attachments 배열이 비어 있으면 detached 상태
                if not igw.get('Attachments'):
                    igw_id = igw['InternetGatewayId']
                    # Name 태그 추출 (없으면 '( - )' 표시)
                    tags = igw.get('Tags', [])
                    name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), "( - )")

                    # IGW ID와 이름을 함께 저장
                    detached_igws.append({
                        "InternetGatewayId": igw_id,
                        "Name": name
                    })

            if not detached_igws:
                print("[✓ COMPLIANT] 3.5 모든 인터넷 게이트웨이가 VPC에 정상적으로 연결되어 있습니다.")
            else:
                print(f"[⚠ WARNING] 3.5 VPC에 연결되지 않은 불필요한 인터넷 게이트웨이가 존재합니다 ({len(detached_igws)}개).")
                for igw in detached_igws:
                    print(f"  ├─ IGW ID: {igw['InternetGatewayId']} (이름: {igw['Name']})")

            has_issues = len(detached_igws) > 0
            risk_level = self.calculate_risk_level(len(detached_igws))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"연결되지 않은 인터넷 게이트웨이 {len(detached_igws)}개 발견" if has_issues else "모든 인터넷 게이트웨이가 VPC에 정상적으로 연결되어 있습니다",
                'detached_igws': detached_igws,
                'summary': f"총 {len(detached_igws)}개의 미사용 인터넷 게이트웨이가 발견되었습니다." if has_issues else "모든 인터넷 게이트웨이가 정상적으로 연결되어 있습니다.",
                'details': {
                    'total_detached_igws': len(detached_igws),
                    'igw_details': detached_igws
                }
            }

        except ClientError as e:
            print(f"[ERROR] 인터넷 게이트웨이 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"인터넷 게이트웨이 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [3.5] 인터넷 게이트웨이 연결 관리 조치
        - 미사용 IGW를 사용자 확인 후 삭제
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('detached_igws'):
            return {'status': 'no_action', 'message': '삭제할 인터넷 게이트웨이가 없습니다.'}

        detached_igws = diagnosis_result['detached_igws']
        ec2 = self.session.client('ec2')
        results = []
        
        print("[FIX] 3.5 연결되지 않은 인터넷 게이트웨이에 대한 조치를 시작합니다.")
        
        for igw in detached_igws:
            igw_id = igw['InternetGatewayId']
            name = igw['Name']
            
            # 선택된 항목인지 확인
            if any(igw_id in str(item) for item in selected_items.values() for item in item):
                try:
                    ec2.delete_internet_gateway(InternetGatewayId=igw_id)
                    print(f"     [SUCCESS] IGW '{igw_id}' (이름: {name})를 삭제했습니다.")
                    results.append({
                        'status': 'success',
                        'resource': f"IGW {igw_id}",
                        'action': f"인터넷 게이트웨이 삭제",
                        'message': f"IGW '{igw_id}' (이름: {name})를 삭제했습니다."
                    })
                    
                except ClientError as e:
                    print(f"     [ERROR] IGW '{igw_id}' 삭제 실패: {e}")
                    results.append({
                        'status': 'error',
                        'resource': f"IGW {igw_id}",
                        'error': str(e),
                        'message': f"IGW '{igw_id}' 삭제 실패: {str(e)}"
                    })
            else:
                print(f"     [INFO] IGW '{igw_id}' 삭제를 건너뜁니다.")

        return {
            'status': 'success',
            'results': results,
            'message': f"{len(results)}개 항목에 대한 조치가 완료되었습니다."
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('detached_igws'):
            return []
            
        detached_igws = diagnosis_result['detached_igws']
        
        return [{
            'id': 'delete_detached_igws',
            'title': '미사용 인터넷 게이트웨이 삭제',
            'description': 'VPC에 연결되지 않은 불필요한 인터넷 게이트웨이를 삭제합니다.',
            'items': [
                {
                    'id': igw['InternetGatewayId'],
                    'name': f"IGW {igw['InternetGatewayId']}",
                    'description': f"이름: {igw['Name']} - VPC에 연결되지 않음"
                }
                for igw in detached_igws
            ]
        }]