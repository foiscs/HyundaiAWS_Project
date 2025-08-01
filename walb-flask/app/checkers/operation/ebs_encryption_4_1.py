"""
[4.1] EBS 및 볼륨 암호화 설정 체커
원본: SHIELDUS-AWS-CHECKER/operation/4_1_ebs_encryption.py
"""

import boto3
from botocore.exceptions import ClientError
from app.checkers.base_checker import BaseChecker


class EbsEncryptionChecker(BaseChecker):
    def __init__(self, session=None):
        super().__init__(session)
        
    @property
    def item_code(self):
        return "4.1"
    
    @property 
    def item_name(self):
        return "EBS 및 볼륨 암호화 설정"
        
    def run_diagnosis(self):
        """
        [4.1] EBS 및 볼륨 암호화 설정
        - 리전의 기본 암호화 설정 여부와 암호화되지 않은 EBS 볼륨 존재 여부를 점검
        """
        print("[INFO] 4.1 EBS 및 볼륨 암호화 설정 체크 중...")
        findings = {'non_default_regions': [], 'unencrypted_volumes': []}
        
        try:
            ec2_regions = [r['RegionName'] for r in self.session.client('ec2').describe_regions()['Regions']]
            for region in ec2_regions:
                try:
                    ec2 = self.session.client('ec2', region_name=region)
                    if not ec2.get_ebs_encryption_by_default()['EbsEncryptionByDefault']:
                        findings['non_default_regions'].append(region)
                    
                    paginator = ec2.get_paginator('describe_volumes')
                    for page in paginator.paginate(Filters=[{'Name': 'status', 'Values': ['available', 'in-use']}]):
                        for vol in page['Volumes']:
                            if not vol.get('Encrypted'):
                                findings['unencrypted_volumes'].append({'id': vol['VolumeId'], 'region': region})
                except ClientError as e:
                    if "OptInRequired" not in str(e): 
                        print(f"[ERROR] 리전 '{region}' 점검 중 오류: {e}")
            
            if findings['non_default_regions']:
                print(f"[⚠ WARNING] 4.1 기본 EBS 암호화가 비활성화된 리전: {', '.join(findings['non_default_regions'])}")
            if findings['unencrypted_volumes']:
                print(f"[⚠ WARNING] 4.1 암호화되지 않은 EBS 볼륨이 존재합니다 ({len(findings['unencrypted_volumes'])}개).")
                for v in findings['unencrypted_volumes']: 
                    print(f"  ├─ {v['id']} ({v['region']})")
            else:
                print("[✓ INFO] 4.1 암호화되지 않은 EBS 볼륨이 존재하지 않습니다.")
            
            if not findings['non_default_regions'] and not findings['unencrypted_volumes']:
                print("[✓ COMPLIANT] 4.1 모든 리전의 기본 암호화가 활성화되어 있고, 암호화되지 않은 볼륨이 없습니다.")

            has_issues = bool(findings['non_default_regions'] or findings['unencrypted_volumes'])
            total_issues = len(findings['non_default_regions']) + len(findings['unencrypted_volumes'])
            risk_level = self.calculate_risk_level(total_issues)
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'message': f"EBS 암호화 문제 {total_issues}건 발견" if has_issues else "모든 리전의 기본 암호화가 활성화되어 있고, 암호화되지 않은 볼륨이 없습니다",
                'findings': findings,
                'summary': f"기본 암호화 비활성 리전 {len(findings['non_default_regions'])}개, 미암호화 볼륨 {len(findings['unencrypted_volumes'])}개" if has_issues else "모든 EBS 암호화 설정이 안전합니다.",
                'details': {
                    'non_default_regions_count': len(findings['non_default_regions']),
                    'unencrypted_volumes_count': len(findings['unencrypted_volumes']),
                    'total_issues': total_issues,
                    'checked_regions': len(ec2_regions)
                }
            }
                
        except ClientError as e:
            print(f"[ERROR] EBS 점검 중 오류 발생: {e}")
            return {
                'status': 'error',
                'error_message': f"EBS 점검 중 오류 발생: {str(e)}"
            }

    def execute_fix(self, selected_items):
        """
        [4.1] EBS 및 볼륨 암호화 설정 조치
        - 기본 암호화 활성화, 미암호화 볼륨은 수동 조치 안내
        """
        if not selected_items:
            return {'status': 'no_action', 'message': '선택된 항목이 없습니다.'}

        # 진단 재실행으로 최신 데이터 확보
        diagnosis_result = self.run_diagnosis()
        if diagnosis_result['status'] != 'success' or not diagnosis_result.get('findings'):
            return {'status': 'no_action', 'message': 'EBS 암호화 조치가 필요한 항목이 없습니다.'}

        findings = diagnosis_result['findings']
        results = []

        if findings['non_default_regions']:
            print("[FIX] 4.1 기본 EBS 암호화 설정 조치를 시작합니다.")
            
            for region in findings['non_default_regions']:
                # 선택된 항목인지 확인
                if any(region in str(item) for item in selected_items.values() for item in item):
                    try:
                        self.session.client('ec2', region_name=region).enable_ebs_encryption_by_default()
                        print(f"     [SUCCESS] 리전 '{region}'의 기본 암호화를 활성화했습니다.")
                        results.append({
                            'status': 'success',
                            'resource': f"Region {region}",
                            'action': '기본 EBS 암호화 활성화',
                            'message': f"리전 '{region}'의 기본 EBS 암호화를 활성화했습니다."
                        })
                    except ClientError as e:
                        print(f"     [ERROR] 실패: {e}")
                        results.append({
                            'status': 'error',
                            'resource': f"Region {region}",
                            'error': str(e),
                            'message': f"리전 '{region}' 기본 암호화 활성화 실패: {str(e)}"
                        })
        
        # 미암호화 볼륨에 대한 수동 가이드
        if findings['unencrypted_volumes']:
            print("[FIX] 4.1 기존의 암호화되지 않은 볼륨은 직접적인 암호화가 불가능하여 수동 조치가 필요합니다.")
            print("  └─ 1. 암호화되지 않은 볼륨의 스냅샷을 생성합니다.")
            print("  └─ 2. 생성된 스냅샷을 '암호화' 옵션을 사용하여 복사합니다.")
            print("  └─ 3. 암호화된 스냅샷으로부터 새 볼륨을 생성합니다.")
            print("  └─ 4. EC2 인스턴스에서 기존 볼륨을 분리(detach)하고 새로 생성한 암호화된 볼륨을 연결(attach)합니다.")
            
            # 수동 조치 안내를 results에 추가
            results.append({
                'item': 'manual_guide',
                'status': 'info',
                'message': f"기본 암호화 설정 {len([r for r in results if r['item'] != 'manual_guide'])}건 완료. 미암호화 볼륨은 수동 조치가 필요합니다."
            })
            return results

        return results

    def _get_manual_guide(self):
        """미암호화 볼륨 수동 조치 가이드 반환"""
        return {
            'title': 'EBS 볼륨 암호화 수동 조치 가이드',
            'description': '기존 미암호화 볼륨을 암호화하려면 스냅샷을 통한 복제 과정이 필요합니다.',
            'steps': [
                {
                    'type': 'warning',
                    'title': '[주의] 서비스 중단 주의',
                    'content': 'EBS 볼륨 교체 과정에서 EC2 인스턴스 중단이 필요할 수 있습니다.'
                },
                {
                    'type': 'step',
                    'title': '1. 스냅샷 생성',
                    'content': 'EC2 콘솔에서 암호화되지 않은 EBS 볼륨의 스냅샷을 생성합니다.'
                },
                {
                    'type': 'step',
                    'title': '2. 암호화된 스냅샷 복사',
                    'content': '생성된 스냅샷을 "암호화" 옵션을 활성화하여 복사합니다.'
                },
                {
                    'type': 'step',
                    'title': '3. 암호화된 볼륨 생성',
                    'content': '암호화된 스냅샷으로부터 새로운 EBS 볼륨을 생성합니다.'
                },
                {
                    'type': 'step',
                    'title': '4. 볼륨 교체',
                    'content': 'EC2 인스턴스를 중지하고 기존 볼륨을 분리한 후 새 암호화된 볼륨을 연결합니다.'
                },
                {
                    'type': 'info',
                    'title': '[참고] 기본 암호화 활성화',
                    'content': '향후 생성되는 모든 EBS 볼륨이 자동으로 암호화되도록 각 리전에서 기본 암호화를 활성화하세요.'
                }
            ]
        }

    def get_fix_options(self, diagnosis_result):
        """자동 조치 옵션 반환"""
        if not diagnosis_result.get('findings'):
            return []
            
        findings = diagnosis_result.get('findings', {})
        options = []
        
        # 기본 암호화 비활성 리전
        if findings.get('non_default_regions'):
            options.append({
                'id': 'enable_default_encryption',
                'title': '리전별 기본 EBS 암호화 활성화',
                'description': '선택한 리전에서 기본 EBS 암호화를 활성화합니다.',
                'items': [
                    {
                        'id': region,
                        'name': f"리전 {region}",
                        'description': f"기본 EBS 암호화 비활성화됨"
                    }
                    for region in findings['non_default_regions']
                ]
            })
        
        # 미암호화 볼륨 (수동 조치만)
        if findings.get('unencrypted_volumes'):
            options.append({
                'id': 'manual_volume_encryption',
                'title': '미암호화 볼륨 수동 조치',
                'description': f'{len(findings["unencrypted_volumes"])}개의 미암호화 볼륨에 대한 수동 조치가 필요합니다.',
                'is_manual': True,
                'items': [
                    {
                        'id': f"{vol['id']}-{vol['region']}",
                        'name': f"볼륨 {vol['id']}",
                        'description': f"리전: {vol['region']} - 수동 암호화 필요"
                    }
                    for vol in findings['unencrypted_volumes']
                ]
            })
        
        return options