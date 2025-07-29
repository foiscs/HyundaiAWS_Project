"""
[3.8] RDS 서브넷 가용 영역 관리 체커  
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_8_rds_subnet_az.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class RdsSubnetAzChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "3.8"
    
    @property 
    def item_name(self):
        return "RDS 서브넷 가용 영역 관리"
        
    def run_diagnosis(self):
        """
        [3.8] RDS 서브넷 가용 영역 관리 (수동 진단)
        - 각 RDS DB 서브넷 그룹이 어떤 가용 영역(AZ)들로 구성되어 있는지 정보를 출력하여 관리자가 직접 판단하도록 안내
        """
        print("[INFO] 3.8 RDS 서브넷 가용 영역 관리 체크 중...")
        rds = self.session.client('rds')
        subnet_groups_to_review = []
        subnet_group_details = []

        try:
            response = rds.describe_db_subnet_groups()
            if not response['DBSubnetGroups']:
                print("[✓ COMPLIANT] 3.8 점검할 RDS DB 서브넷 그룹이 없습니다.")
                return {
                    'status': 'success',
                    'has_issues': False,
                    'risk_level': 'low',
                    'message': '점검할 RDS DB 서브넷 그룹이 없습니다',
                    'subnet_groups_to_review': [],
                    'subnet_group_details': [],
                    'summary': 'RDS DB 서브넷 그룹이 존재하지 않습니다.',
                    'details': {'total_subnet_groups': 0}
                }

            print("[ⓘ MANUAL] 이 항목은 수동 진단이 필요합니다. 각 서브넷 그룹의 가용 영역 구성을 검토하세요.")
            print("-" * 40)
            
            for group in response['DBSubnetGroups']:
                group_name = group['DBSubnetGroupName']
                # 각 서브넷의 가용 영역(AZ)을 추출하여 중복을 제거하고 정렬
                az_set = {subnet['SubnetAvailabilityZone']['Name'] for subnet in group['Subnets']}
                az_list_sorted = sorted(list(az_set))
                
                # 관리자가 판단할 수 있도록 정보 출력
                print(f"  -> 서브넷 그룹: '{group_name}'")
                print(f"     └─ 사용 중인 가용 영역: {', '.join(az_list_sorted)} ({len(az_list_sorted)}개)")
                
                subnet_groups_to_review.append(group_name)
                subnet_group_details.append({
                    'group_name': group_name,
                    'availability_zones': az_list_sorted,
                    'az_count': len(az_list_sorted),
                    'subnets': [{'subnet_id': subnet['SubnetIdentifier'], 'az': subnet['SubnetAvailabilityZone']['Name']} for subnet in group['Subnets']]
                })

            print("-" * 40)
            print("  [양호 기준]: RDS 서브넷 그룹 내에 불필요한 가용 영역이 존재하지 않는 경우.")
            print("  [취약 기준]: RDS 서브넷 그룹 내에 불필요한 가용 영역이 존재하는 경우. (예: 특정 AZ의 서브넷은 더 이상 사용하지 않음)")
            
            # 수동 점검이므로 has_issues는 True로 설정하여 관리자가 검토하도록 함
            has_issues = len(subnet_groups_to_review) > 0
            risk_level = 'medium'  # 수동 검토 필요한 항목은 중간 위험도
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"수동 검토가 필요한 RDS 서브넷 그룹 {len(subnet_groups_to_review)}개" if has_issues else "점검할 RDS DB 서브넷 그룹이 없습니다",
                'subnet_groups_to_review': subnet_groups_to_review,
                'subnet_group_details': subnet_group_details,
                'summary': f"총 {len(subnet_groups_to_review)}개의 RDS DB 서브넷 그룹에 대한 수동 검토가 필요합니다." if has_issues else "검토할 서브넷 그룹이 없습니다.",
                'details': {
                    'total_subnet_groups': len(subnet_groups_to_review),
                    'requires_manual_review': True,
                    'subnet_group_details': subnet_group_details
                }
            }

        except ClientError as e:
            print(f"[ERROR] RDS DB 서브넷 그룹 정보를 가져오는 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"RDS DB 서브넷 그룹 정보를 가져오는 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [3.8] RDS 서브넷 가용 영역 관리 조치
        - 서브넷 그룹 수정은 수동으로 진행하도록 상세히 안내
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('subnet_groups_to_review'):
            return {'status': 'no_action', 'message': '검토할 RDS 서브넷 그룹이 없습니다.'}

        print("[FIX] 3.8 DB 서브넷 그룹의 가용 영역 수정은 수동 조치가 필요합니다.")
        print("  └─ 1. AWS Management Console에서 RDS 서비스로 이동합니다.")
        print("  └─ 2. 왼쪽 메뉴에서 [서브넷 그룹]을 선택합니다.")
        print("  └─ 3. 수정이 필요한 서브넷 그룹을 선택하고 [편집] 버튼을 클릭합니다.")
        print("  └─ 4. '서브넷 추가' 섹션에서 불필요한 가용 영역에 속한 서브넷을 선택 해제하거나, 필요한 서브넷을 추가합니다.")
        print("  └─ 5. [저장]을 클릭하여 변경 사항을 적용합니다.")

        return {
            'status': 'manual_required',
            'message': 'RDS 서브넷 그룹 수정은 수동 조치가 필요합니다.',
            'manual_guide': self._get_manual_guide()
        }

    def _get_manual_guide(self):
        """수동 조치 가이드 반환"""
        return {
            'title': 'RDS 서브넷 가용 영역 수동 검토 가이드',
            'description': 'RDS DB 서브넷 그룹의 가용 영역 구성을 검토하고 필요시 수정하세요.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 수동 검토 필요',
                    'content': 'RDS 서브넷 그룹의 가용 영역 구성은 자동으로 판단할 수 없어 관리자의 직접 검토가 필요합니다.'
                },
                {
                    'type': 'step',
                    'title': '1. AWS 콘솔 접속',
                    'content': 'AWS Management Console에서 RDS 서비스로 이동합니다.'
                },
                {
                    'type': 'step',
                    'title': '2. 서브넷 그룹 확인',
                    'content': '왼쪽 메뉴에서 [서브넷 그룹]을 선택하여 현재 서브넷 그룹 목록을 확인합니다.'
                },
                {
                    'type': 'step',
                    'title': '3. 가용 영역 검토',
                    'content': '각 서브넷 그룹이 사용하는 가용 영역이 실제 필요한 구성인지 검토합니다.'
                },
                {
                    'type': 'step',
                    'title': '4. 불필요한 서브넷 제거',
                    'content': '더 이상 사용하지 않는 가용 영역의 서브넷이 있다면 서브넷 그룹에서 제거합니다.'
                },
                {
                    'type': 'info',
                    'title': '[참고] 가용 영역 최적화',
                    'content': 'RDS는 Multi-AZ 배포를 위해 최소 2개의 가용 영역이 필요하지만, 불필요한 AZ는 제거하여 관리 복잡성을 줄일 수 있습니다.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """수동 조치 옵션 반환"""
        if not diagnosis_result.get('subnet_groups_to_review'):
            return []
            
        subnet_groups = diagnosis_result.get('subnet_groups_to_review', [])
        subnet_group_details = diagnosis_result.get('subnet_group_details', [])
        
        return [{
            'id': 'manual_review_rds_subnet_groups',
            'title': 'RDS 서브넷 그룹 수동 검토',
            'description': 'RDS DB 서브넷 그룹의 가용 영역 구성을 수동으로 검토합니다.',
            'is_manual': True,
            'items': [
                {
                    'id': detail['group_name'],
                    'name': f"서브넷 그룹 {detail['group_name']}",
                    'description': f"가용 영역 {detail['az_count']}개: {', '.join(detail['availability_zones'])}"
                }
                for detail in subnet_group_details
            ]
        }]