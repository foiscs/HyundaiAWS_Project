"""
1.3 IAM 사용자 식별 체커
IAM 사용자의 식별 및 인증 설정을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from ..base_checker import BaseChecker

class IAMIdentificationChecker(BaseChecker):
    """1.3 IAM 사용자 식별 체커"""
    
    @property
    def item_code(self):
        return "1.3"
    
    @property 
    def item_name(self):
        return "IAM 사용자 식별"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            untagged_users = []
            all_users = []
            
            # IAM 사용자 목록 조회
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    user_name = user['UserName']
                    all_users.append(user_name)
                    
                    try:
                        # 사용자 태그 확인
                        tags_response = iam.list_user_tags(UserName=user_name)
                        if not tags_response.get('Tags'):
                            untagged_users.append({
                                'username': user_name,
                                'creation_date': user['CreateDate'].strftime('%Y-%m-%d'),
                                'user_id': user.get('UserId', 'N/A')
                            })
                    except Exception:
                        # 개별 사용자 태그 조회 실패 시 태그 없음으로 간주
                        untagged_users.append({
                            'username': user_name,
                            'creation_date': user['CreateDate'].strftime('%Y-%m-%d'),
                            'user_id': user.get('UserId', 'N/A')
                        })
            
            # 결과 분석
            has_issues = len(untagged_users) > 0
            risk_level = self.calculate_risk_level(len(untagged_users), severity_score=0.5)  # 낮은 위험도
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_users': len(all_users),
                'untagged_users': untagged_users,
                'untagged_count': len(untagged_users),
                'tagged_count': len(all_users) - len(untagged_users),
                'recommendation': "모든 IAM 사용자에게 식별을 위한 태그(이름, 부서, 역할 등)를 추가하는 것을 권장합니다."
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'IAM 정보를 조회하는 중 오류가 발생했습니다: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if result.get('has_issues'):
            untagged_count = result.get('untagged_count', 0)
            untagged_users = result.get('untagged_users', [])
            summary = f"[⚠ WARNING] 1.3 태그가 없는 사용자 계정 존재 ({untagged_count}개)"
            user_list = [user['username'] for user in untagged_users]
            summary += f"\n  ├─ 태그 없는 사용자: {', '.join(user_list)}"
            return summary
        else:
            return "[✓ COMPLIANT] 1.3 모든 사용자 계정에 태그가 존재합니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_users': {
                'count': result.get('total_users', 0),
                'description': '전체 IAM 사용자 수'
            },
            'tagged_users': {
                'count': result.get('tagged_count', 0),
                'description': '태그를 보유한 사용자 수'
            }
        }
        
        if result.get('has_issues'):
            untagged_users = result.get('untagged_users', [])
            details['untagged_users'] = {
                'count': len(untagged_users),
                'users': [user['username'] for user in untagged_users],
                'description': '식별 태그가 없는 사용자',
                'details': untagged_users,
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        untagged_users = result.get('untagged_users', [])
        if not untagged_users:
            return None
        
        # 기본 식별 태그 추가 옵션 제공
        return [{
            'id': 'add_identification_tags',
            'title': '기본 식별 태그 추가',
            'description': f'{len(untagged_users)}개의 사용자에게 기본 식별 태그를 추가합니다.',
            'items': [{'id': user['username'], 'name': user['username'], 'description': f"{user['username']} (생성일: {user['creation_date']})"} for user in untagged_users],
            'action_type': 'add_tags'
        }]
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            results = []
            
            for fix_id, items in selected_items.items():
                if fix_id == 'add_identification_tags':
                    for item in items:
                        user_name = item['id']
                        try:
                            # 기본 식별 태그 추가
                            default_tags = [
                                {'Key': 'Name', 'Value': user_name},
                                {'Key': 'ManagedBy', 'Value': 'WALB'},
                                {'Key': 'Purpose', 'Value': 'IAM User Identification'},
                                {'Key': 'LastReviewed', 'Value': str(datetime.now().date())}
                            ]
                            
                            # 기존 태그가 있는지 확인하고 중복 방지
                            existing_tags = iam.list_user_tags(UserName=user_name).get('Tags', [])
                            existing_keys = {tag['Key'] for tag in existing_tags}
                            
                            new_tags = [tag for tag in default_tags if tag['Key'] not in existing_keys]
                            
                            if new_tags:
                                iam.tag_user(UserName=user_name, Tags=new_tags)
                                
                                results.append({
                                    'item': user_name,
                                    'status': 'success',
                                    'message': f'{user_name} 사용자에게 {len(new_tags)}개의 식별 태그가 추가되었습니다.'
                                })
                            else:
                                results.append({
                                    'item': user_name,
                                    'status': 'success',
                                    'message': f'{user_name} 사용자는 이미 모든 기본 태그를 보유하고 있습니다.'
                                })
                            
                        except ClientError as e:
                            results.append({
                                'item': user_name,
                                'status': 'error',
                                'message': f'{user_name} 태그 추가 실패: {str(e)}'
                            })
            
            return results
            
        except Exception as e:
            return [{
                'item': 'system',
                'status': 'error',
                'message': f'조치 실행 중 오류가 발생했습니다: {str(e)}'
            }]