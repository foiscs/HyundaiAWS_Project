"""
1.5 EC2 키 페어 접근 관리 체커
EC2 인스턴스의 키 페어 접근 권한을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class KeyPairAccessChecker(BaseChecker):
    """1.5 EC2 키 페어 접근 관리 체커"""
    
    @property
    def item_code(self):
        return "1.5"
    
    @property 
    def item_name(self):
        return "EC2 키 페어 접근 관리"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                ec2 = self.session.client('ec2')
            else:
                ec2 = self.session.client('ec2')
            
            instances_without_keypair = []
            all_instances = []
            key_pair_stats = {}
            
            # EC2 인스턴스 목록 조회
            paginator = ec2.get_paginator('describe_instances')
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_id = instance['InstanceId']
                        instance_state = instance['State']['Name']
                        
                        # 실행 중이거나 중지된 인스턴스만 확인
                        if instance_state in ['running', 'stopped']:
                            all_instances.append(instance_id)
                            
                            key_name = instance.get('KeyName')
                            if not key_name:
                                instances_without_keypair.append({
                                    'instance_id': instance_id,
                                    'instance_type': instance.get('InstanceType', 'unknown'),
                                    'state': instance_state,
                                    'launch_time': instance.get('LaunchTime', '').strftime('%Y-%m-%d %H:%M:%S') if instance.get('LaunchTime') else 'unknown',
                                    'vpc_id': instance.get('VpcId', 'unknown'),
                                    'subnet_id': instance.get('SubnetId', 'unknown')
                                })
                            else:
                                # 키 페어별 인스턴스 수 통계
                                if key_name not in key_pair_stats:
                                    key_pair_stats[key_name] = []
                                key_pair_stats[key_name].append(instance_id)
            
            # 키 페어 목록 조회 (참고용)
            try:
                key_pairs_response = ec2.describe_key_pairs()
                total_key_pairs = len(key_pairs_response['KeyPairs'])
                available_key_pairs = [kp['KeyName'] for kp in key_pairs_response['KeyPairs']]
            except Exception:
                total_key_pairs = len(key_pair_stats)
                available_key_pairs = list(key_pair_stats.keys())
            
            # 결과 분석
            has_issues = len(instances_without_keypair) > 0
            risk_level = self.calculate_risk_level(len(instances_without_keypair))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_instances': len(all_instances),
                'total_key_pairs': total_key_pairs,
                'instances_without_keypair': instances_without_keypair,
                'unassigned_count': len(instances_without_keypair),
                'assigned_count': len(all_instances) - len(instances_without_keypair),
                'key_pair_stats': key_pair_stats,
                'available_key_pairs': available_key_pairs,
                'recommendation': "모든 EC2 인스턴스는 적절한 키 페어가 할당되어야 합니다. 키 페어가 없는 인스턴스는 SSH 접근이 제한되어 보안 위험이 될 수 있습니다."
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'EC2 정보를 조회하는 중 오류가 발생했습니다: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if result.get('has_issues'):
            unassigned_count = result.get('unassigned_count', 0)
            total_count = result.get('total_instances', 0)
            return f"⚠️ 전체 {total_count}개 인스턴스 중 {unassigned_count}개가 Key Pair가 할당되지 않았습니다."
        else:
            total_count = result.get('total_instances', 0)
            return f"✅ 모든 {total_count}개 인스턴스에 적절한 Key Pair가 할당되어 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_instances': {
                'count': result.get('total_instances', 0),
                'description': '전체 EC2 인스턴스 수 (running/stopped)'
            },
            'total_key_pairs': {
                'count': result.get('total_key_pairs', 0),
                'description': '사용 가능한 키 페어 수'
            },
            'assigned_instances': {
                'count': result.get('assigned_count', 0),
                'description': '키 페어가 할당된 인스턴스 수'
            }
        }
        
        if result.get('has_issues'):
            unassigned_instances = result.get('instances_without_keypair', [])
            details['unassigned_instances'] = {
                'count': len(unassigned_instances),
                'instances': [inst['instance_id'] for inst in unassigned_instances],
                'description': '키 페어가 할당되지 않은 인스턴스',
                'details': unassigned_instances,
                'recommendation': result.get('recommendation', '')
            }
        
        # 키 페어별 통계 정보 추가
        key_pair_stats = result.get('key_pair_stats', {})
        if key_pair_stats:
            details['key_pair_distribution'] = {
                'key_pairs': len(key_pair_stats),
                'details': {kp: len(instances) for kp, instances in key_pair_stats.items()},
                'description': '키 페어별 인스턴스 분포'
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본 팀원 코드: 자동 조치가 불가능함을 명시
        # Key Pair 할당은 인스턴스 재시작 또는 재배포가 필요하므로 자동 조치가 불가능함
        return None
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 1.5 fix() 함수 내용"""
        if not result.get('has_issues'):
            return None
        
        unassigned_instances = result.get('instances_without_keypair', [])
        if not unassigned_instances:
            return None
        
        # 원본 fix() 함수의 내용을 그대로 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 1.5 Key Pair가 없는 인스턴스 조치',
                'content': 'Key Pair가 없는 인스턴스에 대한 조치는 자동화할 수 없습니다.'
            },
            {
                'type': 'info',
                'title': '수동 조치 안내',
                'content': '실행 중인 인스턴스에 Key Pair를 추가하는 것은 직접적인 방법이 없으므로 아래의 수동 절차를 따르세요.'
            },
            {
                'type': 'step',
                'title': '방법 1. Authorized Keys 직접 수정',
                'content': '실행 중인 인스턴스에 SSH로 접속하여 ~/.ssh/authorized_keys 파일에 새 key pair의 public key를 수동으로 추가합니다.'
            },
            {
                'type': 'step',
                'title': '방법 2. AMI로 새 인스턴스 생성',
                'content': '기존 인스턴스에서 AMI 이미지를 만들어 새로운 인스턴스를 생성할 때 새 key pair를 지정합니다.'
            }
        ]
        
        # 문제가 있는 인스턴스 목록 추가
        if unassigned_instances:
            instance_list = [f"• {inst['instance_id']} ({inst['state']})" for inst in unassigned_instances]
            guide_steps.append({
                'type': 'info',
                'title': f'조치가 필요한 인스턴스 ({len(unassigned_instances)}개)',
                'content': '\n'.join(instance_list)
            })
        
        return {
            'title': '1.5 EC2 Key Pair 접근 관리 수동 조치 가이드',
            'description': '원본 팀원이 작성한 수동 조치 절차를 따라 인스턴스 접근 보안을 강화하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        # 원본 팀원 코드: 자동 조치가 불가능함
        # 수동 조치 안내만 제공
        return [{
            'item': 'manual_fix_notice',
            'status': 'info',
            'message': '[FIX] 1.5 Key Pair가 없는 인스턴스에 대한 조치는 자동화할 수 없습니다.'
        }, {
            'item': 'manual_instructions',
            'status': 'info', 
            'message': '''  └─ 실행 중인 인스턴스에 Key Pair를 추가하는 것은 직접적인 방법이 없으므로 아래의 수동 절차를 따르세요.
  └─ 방법_1. [Authorize_keys 직접 수정]: 실행 중인 인스턴스에 SSH로 접속하여 ~/.ssh/authorized_keys 파일에 새 key pair의 public key를 수동으로 추가
  └─ 방법_2. [AMI로 새 인스턴스 생성]: 기존 인스턴스에서 AMI 이미지를 만들어 새로운 인스턴스를 생성할 때 새 key pair를 지정'''
        }]