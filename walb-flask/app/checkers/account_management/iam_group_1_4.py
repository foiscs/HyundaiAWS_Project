"""
1.4 IAM 그룹 관리 체커
IAM 그룹의 권한 관리 상태를 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class IAMGroupChecker(BaseChecker):
    """1.4 IAM 그룹 관리 체커"""
    
    @property
    def item_code(self):
        return "1.4"
    
    @property 
    def item_name(self):
        return "IAM 그룹 관리"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            ungrouped_users = []
            all_users = []
            group_stats = {}
            
            # IAM 사용자 목록 조회
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    user_name = user['UserName']
                    all_users.append(user_name)
                    
                    try:
                        # 사용자가 속한 그룹 확인
                        groups_response = iam.get_groups_for_user(UserName=user_name)
                        user_groups = groups_response.get('Groups', [])
                        
                        if not user_groups:
                            ungrouped_users.append({
                                'username': user_name,
                                'creation_date': user['CreateDate'].strftime('%Y-%m-%d'),
                                'user_id': user.get('UserId', 'N/A')
                            })
                        else:
                            # 그룹별 사용자 수 통계
                            for group in user_groups:
                                group_name = group['GroupName']
                                if group_name not in group_stats:
                                    group_stats[group_name] = []
                                group_stats[group_name].append(user_name)
                                
                    except Exception:
                        # 개별 사용자 그룹 조회 실패 시 그룹 없음으로 간주
                        ungrouped_users.append({
                            'username': user_name,
                            'creation_date': user['CreateDate'].strftime('%Y-%m-%d'),
                            'user_id': user.get('UserId', 'N/A')
                        })
            
            # IAM 그룹 정보 조회
            try:
                groups_paginator = iam.get_paginator('list_groups')
                total_groups = 0
                for groups_page in groups_paginator.paginate():
                    total_groups += len(groups_page['Groups'])
            except Exception:
                total_groups = len(group_stats)
            
            # 결과 분석
            has_issues = len(ungrouped_users) > 0
            risk_level = self.calculate_risk_level(len(ungrouped_users))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_users': len(all_users),
                'total_groups': total_groups,
                'ungrouped_users': ungrouped_users,
                'ungrouped_count': len(ungrouped_users),
                'grouped_count': len(all_users) - len(ungrouped_users),
                'group_stats': group_stats,
                'recommendation': "모든 IAM 사용자는 적절한 권한 그룹에 속해야 합니다. 개별 사용자에게 직접 정책을 할당하는 것보다 그룹을 통한 권한 관리를 권장합니다."
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
            ungrouped_count = result.get('ungrouped_count', 0)
            total_count = result.get('total_users', 0)
            return f"⚠️ 전체 {total_count}개 사용자 중 {ungrouped_count}개가 IAM 그룹에 속하지 않습니다."
        else:
            total_count = result.get('total_users', 0)
            return f"✅ 모든 {total_count}개 사용자가 적절한 IAM 그룹에 속해 있습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_users': {
                'count': result.get('total_users', 0),
                'description': '전체 IAM 사용자 수'
            },
            'total_groups': {
                'count': result.get('total_groups', 0),
                'description': '전체 IAM 그룹 수'
            },
            'grouped_users': {
                'count': result.get('grouped_count', 0),
                'description': '그룹에 속한 사용자 수'
            }
        }
        
        if result.get('has_issues'):
            ungrouped_users = result.get('ungrouped_users', [])
            details['ungrouped_users'] = {
                'count': len(ungrouped_users),
                'users': [user['username'] for user in ungrouped_users],
                'description': 'IAM 그룹에 속하지 않은 사용자',
                'details': ungrouped_users,
                'recommendation': result.get('recommendation', '')
            }
        
        # 그룹별 통계 정보 추가
        group_stats = result.get('group_stats', {})
        if group_stats:
            details['group_distribution'] = {
                'groups': len(group_stats),
                'details': {group: len(users) for group, users in group_stats.items()},
                'description': '그룹별 사용자 분포'
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        ungrouped_users = result.get('ungrouped_users', [])
        if not ungrouped_users:
            return None
        
        # 기본 그룹 생성 및 할당 옵션 제공
        return [{
            'id': 'assign_to_default_group',
            'title': '기본 그룹에 사용자 할당',
            'description': f'{len(ungrouped_users)}개의 사용자를 기본 그룹(ReadOnlyUsers)에 할당합니다.',
            'items': [{'id': user['username'], 'name': user['username'], 'description': f"{user['username']} (생성일: {user['creation_date']})"} for user in ungrouped_users],
            'action_type': 'assign_group'
        }]
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            results = []
            default_group_name = 'ReadOnlyUsers'
            
            # 원본에서는 대화형으로 사용자가 그룹을 선택/생성하는 방식
            # 웹 인터페이스에서는 이를 수동 조치로 안내
            return [{
                'item': 'manual_group_assignment',
                'status': 'info',
                'message': '[FIX] 1.4 그룹에 속하지 않은 사용자에 대한 조치를 시작합니다.'
            }, {
                'item': 'group_selection_needed',
                'status': 'info',
                'message': '각 사용자별로 적절한 그룹을 선택하거나 새 그룹을 생성해야 합니다.'
            }, {
                'item': 'manual_procedure',
                'status': 'info',
                'message': 'AWS 콘솔 > IAM > 그룹에서 그룹 생성 후, 사용자 탭에서 해당 사용자들을 적절한 그룹에 추가하세요.'
            }]
            
        except Exception as e:
            return [{
                'item': 'system',
                'status': 'error',
                'message': f'조치 실행 중 오류가 발생했습니다: {str(e)}'
            }]