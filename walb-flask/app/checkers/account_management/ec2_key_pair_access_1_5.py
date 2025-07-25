"""
1.5 Key Pair 접근 관리 진단 (Flask용)
mainHub의 ec2_key_pair_access_1_5.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class KeyPairAccessChecker(BaseChecker):
    """1.5 Key Pair 접근 관리 진단"""
    
    @property
    def item_code(self):
        return "1.5"
    
    @property 
    def item_name(self):
        return "Key Pair 접근 관리"
    
    def run_diagnosis(self):
        """
        진단 실행 - 실행 중인 모든 EC2 인스턴스에 Key Pair가 할당되어 있는지 점검
        """
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = boto3.client('ec2')
                
            instances_without_keypair = []
            total_instances = 0
            
            # 실행 중인 인스턴스만 조회
            paginator = ec2.get_paginator('describe_instances')
            pages = paginator.paginate(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )
            
            for page in pages:
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        total_instances += 1
                        if 'KeyName' not in instance:
                            instances_without_keypair.append({
                                'instance_id': instance['InstanceId'],
                                'instance_type': instance.get('InstanceType', 'Unknown'),
                                'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else 'Unknown',
                                'public_ip': instance.get('PublicIpAddress', 'N/A'),
                                'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                                'vpc_id': instance.get('VpcId', 'N/A'),
                                'subnet_id': instance.get('SubnetId', 'N/A'),
                                'security_groups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])]
                            })
            
            # 진단 결과 생성
            issues_count = len(instances_without_keypair)
            risk_level = self.calculate_risk_level(issues_count, severity_score=2)
            
            return {
                "status": "success",
                "instances_without_keypair": instances_without_keypair,
                "total_instances": total_instances,
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
        total_instances = result.get('total_instances', 0)
        issues_count = result.get('issues_count', 0)
        
        if issues_count > 0:
            return f"⚠️ 전체 {total_instances}개 인스턴스 중 {issues_count}개가 Key Pair가 할당되지 않았습니다."
        else:
            return f"✅ 모든 {total_instances}개 인스턴스가 Key Pair를 보유하고 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "인스턴스 통계": {
                "전체 인스턴스 수": result.get('total_instances', 0),
                "Key Pair 미할당": result.get('issues_count', 0),
                "recommendation": "모든 EC2 인스턴스는 보안을 위해 Key Pair가 할당되어야 합니다."
            }
        }
        
        if result.get('instances_without_keypair'):
            details["Key Pair 미할당 인스턴스"] = {}
            for instance in result['instances_without_keypair']:
                instance_id = instance['instance_id']
                details["Key Pair 미할당 인스턴스"][instance_id] = {
                    "instance_type": instance['instance_type'],
                    "public_ip": instance['public_ip'],
                    "private_ip": instance['private_ip'],
                    "vpc_id": instance['vpc_id'],
                    "security_groups": instance['security_groups']
                }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        instances_without_keypair = result.get('instances_without_keypair', [])
        
        if instances_without_keypair:
            return [{
                "type": "terminate_instances",
                "title": "인스턴스 종료",
                "description": f"{len(instances_without_keypair)}개 Key Pair 미할당 인스턴스를 종료합니다.",
                "items": [{"instance_id": inst['instance_id'], 
                          "instance_type": inst['instance_type'],
                          "action": "인스턴스 종료"} 
                         for inst in instances_without_keypair],
                "severity": "high",
                "warning": "주의: 인스턴스 종료는 되돌릴 수 없습니다. 중요한 데이터가 있는지 확인하세요."
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
            instance_ids = selected_items.get('terminate_instances', [])
            
            for instance_id in instance_ids:
                try:
                    ec2.terminate_instances(InstanceIds=[instance_id])
                    results.append({
                        "instance_id": instance_id,
                        "action": "인스턴스 종료",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "instance_id": instance_id,
                        "action": "인스턴스 종료",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "instance_id": "전체",
                "action": "인스턴스 종료",
                "status": "error",
                "error": str(e)
            }]