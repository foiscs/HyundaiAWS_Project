"""
[3.2] 보안 그룹 인/아웃바운드 불필요 정책 관리 체커
원본: SHIELDUS-AWS-CHECKER/virtual_resources/3_2_sg_unnecessary_policy.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class SecurityGroupUnnecessaryPolicyChecker(BaseChecker):
    """[3.2] 보안 그룹 인/아웃바운드 불필요 정책 관리 체커"""
    
    @property
    def item_code(self):
        return "3.2"
    
    @property 
    def item_name(self):
        return "보안 그룹 인/아웃바운드 불필요 정책 관리"
    
    def run_diagnosis(self):
        """
        [3.2] 보안 그룹 인/아웃바운드 불필요 정책 관리
        - ANY IP 규칙을 가진 미사용 보안 그룹 점검
        """
        print("[INFO] 3.2 보안 그룹 인/아웃바운드 불필요 정책 관리 체크 중...")
        
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = self.session.client('ec2')
                
            deletable = []

            all_sgs = ec2.describe_security_groups()['SecurityGroups']

            for sg in all_sgs:
                sg_id = sg['GroupId']
                sg_name = sg.get('GroupName', 'N/A')

                # ANY IP 규칙 포함 여부 확인
                matched = any(
                    any(ip.get('CidrIp') == '0.0.0.0/0' for ip in rule.get('IpRanges', [])) or
                    any(ip.get('CidrIpv6') == '::/0' for ip in rule.get('Ipv6Ranges', []))
                    for rule in sg.get('IpPermissions', []) + sg.get('IpPermissionsEgress', [])
                )
                if not matched:
                    continue

                if sg_name == 'default':
                    print(f"  -> SG '{sg_id}' ({sg_name})는 기본 보안 그룹입니다. 삭제 대상이 아닙니다.")
                    continue

                in_use, used_by = self._is_sg_in_use(ec2, sg_id)
                if in_use:
                    print(f"  -> SG '{sg_id}' ({sg_name})는 리소스({used_by})에 의해 사용 중입니다. 삭제 대상이 아닙니다.")
                    continue

                if not self._can_delete_sg(ec2, sg_id):
                    print(f"  -> SG '{sg_id}' ({sg_name})는 다른 리소스에 의해 참조 중이라 삭제 대상이 아닙니다.")
                    continue

                print(f"  -> SG '{sg_id}' ({sg_name})는 미연결 상태이며 ANY IP가 포함된 규칙이 존재합니다.")
                deletable.append({'GroupId': sg_id, 'GroupName': sg_name})

            if deletable:
                print(f"[!] 삭제 가능한 보안 그룹 {len(deletable)}개가 발견되었습니다.")
            else:
                print("[ⓘ info] 삭제 가능한 보안 그룹이 없습니다.")

            # 결과 분석
            has_issues = len(deletable) > 0
            risk_level = self.calculate_risk_level(len(deletable))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_deletable_sgs': len(deletable),
                'deletable_sgs': deletable,
                'recommendation': "사용되지 않는 보안 그룹 중 ANY IP 규칙을 포함한 것들은 보안 위험을 초래할 수 있으므로 삭제를 권장합니다."
            }

        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'보안 그룹 점검 중 오류 발생: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }

    def _is_sg_in_use(self, ec2, sg_id):
        """보안 그룹이 사용 중인지 확인 - 원본 is_sg_in_use 함수"""
        # 1. ENI
        eni = ec2.describe_network_interfaces(Filters=[{'Name': 'group-id', 'Values': [sg_id]}])
        if eni['NetworkInterfaces']:
            return True, "ENI"

        # 2. EC2
        ec2s = ec2.describe_instances(Filters=[{'Name': 'instance.group-id', 'Values': [sg_id]}])
        for reservation in ec2s.get('Reservations', []):
            if reservation['Instances']:
                return True, "EC2"

        # 3. RDS
        try:
            rds = self.session.client('rds') if not self.session else self.session.client('rds')
            rds_instances = rds.describe_db_instances()
            for db in rds_instances['DBInstances']:
                if any(sg['VpcSecurityGroupId'] == sg_id for sg in db.get('VpcSecurityGroups', [])):
                    return True, "RDS"
        except ClientError:
            pass

        # 4. ELB
        try:
            elb = self.session.client('elbv2') if not self.session else self.session.client('elbv2')
            elbs = elb.describe_load_balancers()
            for lb in elbs['LoadBalancers']:
                if sg_id in lb.get('SecurityGroups', []):
                    return True, "ELB"
        except ClientError:
            pass

        # 5. Lambda
        try:
            lam = self.session.client('lambda') if not self.session else self.session.client('lambda')
            funcs = lam.list_functions()['Functions']
            for fn in funcs:
                cfg = lam.get_function_configuration(FunctionName=fn['FunctionName'])
                if sg_id in cfg.get('VpcConfig', {}).get('SecurityGroupIds', []):
                    return True, "Lambda"
        except ClientError:
            pass

        return False, None

    def _can_delete_sg(self, ec2, sg_id):
        """보안 그룹이 삭제 가능한지 확인 - 원본 can_delete_sg 함수"""
        try:
            # 실제로 삭제하지 않고 삭제 가능성만 확인하기 위해 DryRun 사용
            ec2.delete_security_group(GroupId=sg_id, DryRun=True)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'DryRunOperation':
                # DryRun이 성공하면 실제로 삭제 가능
                return True
            elif e.response['Error']['Code'] == 'DependencyViolation':
                return False
            elif e.response['Error']['Code'] == 'InvalidGroup.NotFound':
                return False
            else:
                return True  # 기타 오류는 사용자 입력에 위임
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if result.get('has_issues'):
            deletable_count = result.get('total_deletable_sgs', 0)
            return f"⚠️ 삭제 가능한 보안 그룹 {deletable_count}개가 발견되었습니다."
        else:
            return f"✅ 삭제 가능한 보안 그룹이 없습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_deletable_sgs': {
                'count': result.get('total_deletable_sgs', 0),
                'description': '삭제 가능한 보안 그룹 수'
            }
        }
        
        if result.get('has_issues'):
            deletable_sgs = result.get('deletable_sgs', [])
            details['deletable_sgs_details'] = {
                'count': len(deletable_sgs),
                'sgs': [{
                    'group_id': sg['GroupId'],
                    'group_name': sg['GroupName']
                } for sg in deletable_sgs],
                'description': '삭제 가능한 보안 그룹 상세 정보',
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return []
        
        deletable_sgs = result.get('deletable_sgs', [])
        if not deletable_sgs:
            return []
        
        return [{
            'id': 'delete_unused_sgs',
            'title': '미사용 보안 그룹 삭제',
            'description': 'ANY IP 규칙을 가진 미사용 보안 그룹을 삭제합니다.',
            'items': [
                {
                    'id': sg['GroupId'],
                    'name': f"SG {sg['GroupId']} ({sg['GroupName']})",
                    'description': f"미사용 보안 그룹 - ANY IP 규칙 포함"
                }
                for sg in deletable_sgs
            ]
        }]
    
    def execute_fix(self, selected_items):
        """
        [3.2] 보안 그룹 불필요 정책 관리 조치
        - 사용자 확인 후 삭제 가능한 보안 그룹을 삭제
        """
        if not selected_items:
            return [{
                'item': 'no_selection',
                'status': 'info',
                'message': '선택된 항목이 없습니다.'
            }]

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('deletable_sgs'):
            return [{
                'item': 'no_action_needed',
                'status': 'info',
                'message': '삭제할 보안 그룹이 없습니다.'
            }]

        deletable_sgs = diagnosis_result['deletable_sgs']
        
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = self.session.client('ec2')
        except Exception as e:
            return [{
                'item': 'connection_error',
                'status': 'error',
                'message': f'AWS 연결 실패: {str(e)}'
            }]
        
        results = []
        print("[FIX] 3.2 삭제 가능한 보안 그룹에 대해 사용자 동의를 받고 삭제합니다.")
        
        for sg in deletable_sgs:
            sg_id = sg['GroupId']
            sg_name = sg['GroupName']
            
            # 선택된 항목인지 확인
            if any(sg_id in str(item) for item_list in selected_items.values() for item in item_list):
                try:
                    # 원본 fix 함수의 로직 그대로 구현
                    ec2.delete_security_group(GroupId=sg_id)
                    print(f"     [SUCCESS] SG '{sg_id}'를 삭제했습니다.")
                    results.append({
                        'item': f"SG {sg_id}",
                        'status': 'success',
                        'message': f"SG '{sg_id}' ({sg_name})를 삭제했습니다."
                    })
                    
                except ClientError as e:
                    print(f"     [ERROR] SG '{sg_id}' 삭제 실패: {e}")
                    results.append({
                        'item': f"SG {sg_id}",
                        'status': 'error',
                        'message': f"SG '{sg_id}' 삭제 실패: {str(e)}"
                    })
            else:
                print(f"     [SKIPPED] SG '{sg_id}' 삭제를 건너뜁니다.")

        return results