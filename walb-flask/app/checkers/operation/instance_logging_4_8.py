"""
[4.8] 인스턴스 로깅 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_8_instance_logging.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class InstanceLoggingChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.8"
    
    @property 
    def item_name(self):
        return "인스턴스 로깅 설정"
        
    def run_diagnosis(self):
        """
        [4.8] 인스턴스 로깅 설정 (수동 점검 안내)
        """
        print("[INFO] 4.8 인스턴스 로깅 설정 체크 중...")
        
        try:
            logs_client = self.session.client('logs')
            ec2_client = self.session.client('ec2')

            # 1. 모든 CloudWatch 로그 그룹 이름 수집
            log_groups = []
            next_token = None
            while True:
                if next_token:
                    response = logs_client.describe_log_groups(nextToken=next_token)
                else:
                    response = logs_client.describe_log_groups()
                log_groups.extend(response.get('logGroups', []))
                next_token = response.get('nextToken')
                if not next_token:
                    break
            log_group_names = [lg['logGroupName'] for lg in log_groups]

            # 2. EC2 인스턴스 ID 수집
            instances = ec2_client.describe_instances()
            instance_ids = [
                inst['InstanceId']
                for reservation in instances['Reservations']
                for inst in reservation['Instances']
            ]

            # 3. 로그 그룹 이름에 인스턴스 ID 포함 여부로 로깅 여부 확인
            good = [iid for iid in instance_ids if any(iid in lg for lg in log_group_names)]
            bad = list(set(instance_ids) - set(good))

            # 결과 출력
            print("✅ 양호 (CloudWatch 로그 등록됨):", good)
            print("❌ 취약 (로그 등록 안 됨):", bad)
            
            print("[ⓘ MANUAL] EC2 인스턴스 내부의 로그 설정은 자동 점검이 불가능합니다.")
            print("  └─ CloudWatch 콘솔의 로그 그룹 목록에 EC2 인스턴스 관련 로그(예: /var/log/messages)가 수집되고 있는지 확인하세요.")

            has_issues = len(bad) > 0
            total_issues = len(bad)
            risk_level = self.calculate_risk_level(total_issues)
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"로그 등록이 안 된 인스턴스 {total_issues}개 발견" if has_issues else "모든 인스턴스가 CloudWatch 로그에 등록되어 있습니다",
                'findings': {"양호": good, "취약": bad},
                'summary': f"로그 등록 안 됨 {len(bad)}개, 양호 {len(good)}개" if has_issues else "모든 인스턴스 로깅이 정상적으로 설정되어 있습니다.",
                'details': {
                    'good_instances_count': len(good),
                    'bad_instances_count': len(bad),
                    'total_instances': len(instance_ids),
                    'total_log_groups': len(log_group_names)
                }
            }
                
        except ClientError as e:
            print(f"[ERROR] 인스턴스 로깅 점검 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"인스턴스 로깅 점검 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.8] 인스턴스 로깅 설정 조치 (수동 조치 안내)
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': '인스턴스 로깅 조치가 필요한 항목이 없습니다.'}

        findings = diagnosis_result['findings']
        
        if findings.get('취약'):
            print("[FIX] 4.8 EC2 인스턴스 로깅 설정 가이드입니다.")
            print("  └─ 1. EC2 인스턴스에 CloudWatch Logs Agent를 전송할 수 있는 IAM 역할(CloudWatchAgentServerPolicy)을 연결합니다.")
            print("  └─ 2. Systems Manager(SSM) Distributor를 사용하거나 직접 접속하여 인스턴스에 CloudWatch Agent를 설치합니다.")
            print("  └─ 3. Agent 구성 파일(/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json)을 생성하여 수집할 로그 파일 경로를 지정합니다.")
            print("  └─ 4. Agent를 시작하여 로그 수집을 개시합니다: sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/path/to/config.json")
            
            return {
                'status': 'manual_required',
                'message': f"{len(findings['취약'])}개 인스턴스에 대한 수동 조치가 필요합니다.",
                'manual_guide': self._get_manual_guide(findings)
            }

        return {
            'status': 'no_action',
            'message': '조치가 필요한 항목이 없습니다.'
        }

    def _get_manual_guide(self, findings=None):
        """인스턴스 로깅 수동 조치 가이드 반환"""
        return {
            'title': 'EC2 인스턴스 로깅 설정 수동 조치 가이드',
            'description': 'EC2 인스턴스의 로그를 CloudWatch로 전송하려면 CloudWatch Agent 설치 및 설정이 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] IAM 역할 필요',
                    'content': 'CloudWatch Logs Agent가 로그를 전송하려면 적절한 IAM 역할이 EC2 인스턴스에 연결되어 있어야 합니다.'
                },
                {
                    'type': 'step',
                    'title': '1. IAM 역할 연결',
                    'content': 'EC2 인스턴스에 CloudWatchAgentServerPolicy 정책이 포함된 IAM 역할을 연결합니다.'
                },
                {
                    'type': 'step',
                    'title': '2. CloudWatch Agent 설치',
                    'content': 'Systems Manager(SSM) Distributor를 사용하거나 직접 SSH 접속하여 CloudWatch Agent를 설치합니다.'
                },
                {
                    'type': 'step',
                    'title': '3. Agent 구성 파일 생성',
                    'content': '/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json 파일을 생성하여 수집할 로그 파일 경로를 지정합니다.'
                },
                {
                    'type': 'commands',
                    'title': '4. Agent 시작 명령어',
                    'content': [
                        'sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/path/to/config.json'
                    ]
                },
                {
                    'type': 'info',
                    'title': '[참고] 자동 점검 제한',
                    'content': 'EC2 인스턴스 내부의 로그 설정은 자동 점검이 불가능하므로 CloudWatch 콘솔에서 로그 그룹을 확인하세요.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환 (수동 조치만 가능)"""
        if not diagnosis_result.get('findings'):
            return []
            
        findings = diagnosis_result.get('findings', {})
        options = []
        
        # 로그 등록이 안 된 인스턴스 (수동 조치만)
        if findings.get('취약'):
            options.append({
                'id': 'manual_instance_logging',
                'title': '인스턴스 로깅 수동 설정',
                'description': f'{len(findings["취약"])}개의 인스턴스에 대한 CloudWatch Agent 설정이 필요합니다.',
                'is_manual': True,
                'items': [
                    {
                        'id': instance_id,
                        'name': f"인스턴스 {instance_id}",
                        'description': "CloudWatch 로그 등록 필요"
                    }
                    for instance_id in findings['취약']
                ]
            })
        
        return options

    @property
    def item_code(self):
        return "4.8"
    
    @property 
    def item_name(self):
        return "인스턴스 로깅 설정"