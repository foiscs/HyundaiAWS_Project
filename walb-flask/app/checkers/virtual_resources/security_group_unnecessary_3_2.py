"""
3.2 보안 그룹 불필요한 설정 관리 진단 (Flask용)
mainHub의 security_group_unnecessary_3_2.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class SecurityGroupUnnecessaryChecker(BaseChecker):
    """3.2 보안 그룹 불필요한 설정 관리 진단"""
    
    @property
    def item_code(self):
        return "3.2"
    
    @property 
    def item_name(self):
        return "보안 그룹 불필요한 설정 관리"
    
    def run_diagnosis(self):
        """
        진단 수행
        - 사용되지 않는 보안 그룹과 불필요한 규칙 점검
        """
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            unused_security_groups = []
            total_security_groups = 0
            
            # 모든 보안 그룹 조회
            paginator = ec2.get_paginator('describe_security_groups')
            all_security_groups = {}
            
            for page in paginator.paginate():
                for sg in page['SecurityGroups']:
                    total_security_groups += 1
                    all_security_groups[sg['GroupId']] = sg
            
            # 사용 중인 보안 그룹 ID 수집
            used_sg_ids = set()
            
            # EC2 인스턴스에서 사용 중인 보안 그룹
            try:
                instances_paginator = ec2.get_paginator('describe_instances')
                for page in instances_paginator.paginate():
                    for reservation in page['Reservations']:
                        for instance in reservation['Instances']:
                            if instance['State']['Name'] != 'terminated':
                                for sg in instance.get('SecurityGroups', []):
                                    used_sg_ids.add(sg['GroupId'])
            except ClientError:
                pass  # 권한이 없으면 스킵
            
            # RDS 인스턴스에서 사용 중인 보안 그룹
            try:
                rds = self.session.client('rds') if self.session else boto3.client('rds')
                rds_paginator = rds.get_paginator('describe_db_instances')
                for page in rds_paginator.paginate():
                    for db in page['DBInstances']:
                        for sg in db.get('VpcSecurityGroups', []):
                            used_sg_ids.add(sg['VpcSecurityGroupId'])
            except ClientError:
                pass  # 권한이 없으면 스킵
            
            # ELB에서 사용 중인 보안 그룹
            try:
                elb = self.session.client('elbv2') if self.session else boto3.client('elbv2')
                elb_paginator = elb.get_paginator('describe_load_balancers')
                for page in elb_paginator.paginate():
                    for lb in page['LoadBalancers']:
                        for sg_id in lb.get('SecurityGroups', []):
                            used_sg_ids.add(sg_id)
            except ClientError:
                pass  # 권한이 없으면 스킵
            
            # 사용되지 않는 보안 그룹 찾기
            for sg_id, sg in all_security_groups.items():
                # 기본 보안 그룹은 제외
                if sg['GroupName'] == 'default':
                    continue
                
                # 사용되지 않는 보안 그룹
                if sg_id not in used_sg_ids:
                    unused_security_groups.append({
                        'GroupId': sg_id,
                        'GroupName': sg['GroupName'],
                        'Description': sg['Description'],
                        'VpcId': sg.get('VpcId', 'EC2-Classic'),
                        'IpPermissions': len(sg.get('IpPermissions', [])),
                        'IpPermissionsEgress': len(sg.get('IpPermissionsEgress', []))
                    })
            
            # 위험도 계산
            issues_count = len(unused_security_groups)
            risk_level = self.calculate_risk_level(
                issues_count,
                1  # 불필요한 리소스는 낮은 위험도
            )
            
            return {
                "status": "success",
                "unused_security_groups": unused_security_groups,
                "total_security_groups": total_security_groups,
                "used_security_groups": len(used_sg_ids),
                "issues_count": issues_count,
                "risk_level": risk_level,
                "has_issues": issues_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        total_sgs = result.get('total_security_groups', 0)
        used_sgs = result.get('used_security_groups', 0)
        unused_count = result.get('issues_count', 0)
        
        if unused_count > 0:
            return f"⚠️ 전체 {total_sgs}개 보안 그룹 중 {unused_count}개가 사용되지 않고 있습니다. (사용 중: {used_sgs}개)"
        else:
            return f"✅ 모든 {total_sgs}개 보안 그룹이 사용되고 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "보안 그룹 사용 현황": {
                "전체 보안 그룹": result.get('total_security_groups', 0),
                "사용 중인 보안 그룹": result.get('used_security_groups', 0),
                "사용되지 않는 보안 그룹": result.get('issues_count', 0),
                "recommendation": "사용되지 않는 보안 그룹은 삭제하여 관리 복잡성을 줄이세요."
            }
        }
        
        if result.get('unused_security_groups'):
            details["사용되지 않는 보안 그룹"] = {}
            for sg in result['unused_security_groups']:
                sg_key = f"{sg['GroupId']} ({sg['GroupName']})"
                details["사용되지 않는 보안 그룹"][sg_key] = {
                    "설명": sg['Description'],
                    "VPC": sg['VpcId'],
                    "인바운드 규칙 수": sg['IpPermissions'],
                    "아웃바운드 규칙 수": sg['IpPermissionsEgress']
                }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        unused_sgs = result.get('unused_security_groups', [])
        
        if unused_sgs:
            return [{
                "type": "delete_unused_security_groups",
                "title": "사용되지 않는 보안 그룹 삭제",
                "description": f"{len(unused_sgs)}개의 사용되지 않는 보안 그룹을 삭제합니다.",
                "items": [{"group_id": sg['GroupId'], 
                          "group_name": sg['GroupName'],
                          "vpc_id": sg['VpcId'],
                          "action": "보안 그룹 삭제"} 
                         for sg in unused_sgs],
                "severity": "low",
                "warning": "주의: 보안 그룹 삭제는 되돌릴 수 없습니다."
            }]
        
        return None
    
    def execute_fix(self, selected_items):
        """조치 실행"""
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
            
            results = []
            sgs_to_delete = selected_items.get('unused_security_groups', [])
            
            for sg_info in sgs_to_delete:
                try:
                    group_id = sg_info['GroupId']
                    ec2.delete_security_group(GroupId=group_id)
                    
                    results.append({
                        "group_id": group_id,
                        "group_name": sg_info.get('GroupName', ''),
                        "action": "보안 그룹 삭제",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "group_id": sg_info.get('GroupId', 'unknown'),
                        "group_name": sg_info.get('GroupName', ''),
                        "action": "보안 그룹 삭제",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "group_id": "전체",
                "action": "보안 그룹 삭제",
                "status": "error",
                "error": str(e)
            }]