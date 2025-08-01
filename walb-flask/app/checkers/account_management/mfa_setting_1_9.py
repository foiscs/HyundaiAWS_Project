"""
1.9 MFA 설정 체커
Multi-Factor Authentication 설정 상태를 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class MFASettingChecker(BaseChecker):
    """1.9 MFA 설정 체커"""
    
    @property
    def item_code(self):
        return "1.9"
    
    @property 
    def item_name(self):
        return "MFA 설정"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = self.session.client('iam')
            
            users_without_mfa = []
            all_users = []
            mfa_stats = {'virtual': 0, 'hardware': 0, 'none': 0}
            
            # IAM 사용자 목록 조회
            paginator = iam.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page['Users']:
                    user_name = user['UserName']
                    all_users.append(user_name)
                    
                    try:
                        # MFA 디바이스 확인
                        mfa_devices = iam.list_mfa_devices(UserName=user_name)
                        virtual_devices = mfa_devices.get('MFADevices', [])
                        
                        if not virtual_devices:
                            users_without_mfa.append({
                                'username': user_name,
                                'creation_date': user['CreateDate'].strftime('%Y-%m-%d'),
                                'user_id': user.get('UserId', 'N/A'),
                                'has_console_access': self._check_console_access(iam, user_name)
                            })
                            mfa_stats['none'] += 1
                        else:
                            # MFA 디바이스 종류별 통계
                            for device in virtual_devices:
                                if 'arn:aws:iam::' in device.get('SerialNumber', ''):
                                    mfa_stats['virtual'] += 1
                                else:
                                    mfa_stats['hardware'] += 1
                                    
                    except Exception:
                        # MFA 디바이스 조회 실패 시 MFA 없음으로 간주
                        users_without_mfa.append({
                            'username': user_name,
                            'creation_date': user['CreateDate'].strftime('%Y-%m-%d'),
                            'user_id': user.get('UserId', 'N/A'),
                            'has_console_access': False
                        })
                        mfa_stats['none'] += 1
            
            # 결과 분석
            has_issues = len(users_without_mfa) > 0
            risk_level = self.calculate_risk_level(len(users_without_mfa))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_users': len(all_users),
                'users_without_mfa': users_without_mfa,
                'no_mfa_count': len(users_without_mfa),
                'mfa_enabled_count': len(all_users) - len(users_without_mfa),
                'mfa_stats': mfa_stats,
                'recommendation': "모든 IAM 사용자, 특히 콘솔 접근 권한이 있는 사용자는 MFA를 활성화해야 합니다."
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
    
    def _check_console_access(self, iam, user_name):
        """사용자의 콘솔 접근 권한 확인"""
        try:
            # 로그인 프로필 확인
            iam.get_login_profile(UserName=user_name)
            return True
        except:
            return False
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        summary = ""
        
        # 루트 계정 MFA 확인
        if not result.get('mfa_enabled'):
            summary += "[⚠ WARNING] 1.9 Root 계정에 MFA가 활성화되어 있지 않습니다.\n"
        else:
            summary += "[✓ COMPLIANT] 1.9 Root 계정에 MFA가 활성화되어 있습니다.\n"
        
        # 사용자 MFA 확인
        users_without_mfa = result.get('users_without_mfa', [])
        if not users_without_mfa:
            summary += "[✓ COMPLIANT] 1.9 모든 콘솔 접근 가능 IAM 사용자에게 MFA가 활성화되어 있습니다."
        else:
            user_list = [user['username'] for user in users_without_mfa]
            summary += f"[⚠ WARNING] 1.9 MFA가 비활성화된 콘솔 접근 사용자 존재 ({len(users_without_mfa)}명)\n"
            summary += f"  ├─ MFA 비활성 사용자: {', '.join(user_list)}"
        
        return summary
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_users': {
                'count': result.get('total_users', 0),
                'description': '전체 IAM 사용자 수'
            },
            'mfa_enabled_users': {
                'count': result.get('mfa_enabled_count', 0),
                'description': 'MFA가 설정된 사용자 수'
            }
        }
        
        mfa_stats = result.get('mfa_stats', {})
        if mfa_stats:
            details['mfa_statistics'] = {
                'virtual_mfa': mfa_stats.get('virtual', 0),
                'hardware_mfa': mfa_stats.get('hardware', 0),
                'no_mfa': mfa_stats.get('none', 0),
                'description': 'MFA 디바이스 유형별 통계'
            }
        
        if result.get('has_issues'):
            no_mfa_users = result.get('users_without_mfa', [])
            console_users = [user for user in no_mfa_users if user.get('has_console_access')]
            
            details['users_without_mfa'] = {
                'count': len(no_mfa_users),
                'users': [user['username'] for user in no_mfa_users],
                'console_access_users': len(console_users),
                'description': 'MFA가 설정되지 않은 사용자',
                'details': no_mfa_users,
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본: MFA 설정은 사용자의 물리적/가상 디바이스 등록이 필요하므로 자동화할 수 없음
        return None
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 1.9 fix() 함수 내용"""
        if not result.get('has_issues'):
            return None
        
        # 원본 fix() 함수의 내용을 그대로 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 1.9 MFA 설정 수동 조치',
                'content': 'MFA 설정은 사용자의 물리적/가상 디바이스 등록이 필요하므로 자동화할 수 없습니다.'
            }
        ]
        
        # Root 계정 MFA가 비활성화된 경우
        if not result.get('mfa_enabled', True):
            guide_steps.append({
                'type': 'step',
                'title': '[Root 계정] MFA 설정',
                'content': 'AWS Management Console에 Root로 로그인하여 [내 보안 자격 증명]에서 MFA 디바이스를 할당하세요.'
            })
        
        # MFA가 없는 IAM 사용자가 있는 경우
        users_without_mfa = result.get('users_without_mfa', [])
        if users_without_mfa:
            user_list = [user['username'] for user in users_without_mfa]
            guide_steps.append({
                'type': 'step',
                'title': '[IAM 사용자] MFA 설정 안내',
                'content': f'다음 사용자들에게 각자 로그인하여 [내 보안 자격 증명]에서 MFA를 설정하도록 안내하세요: {", ".join(user_list)}'
            })
        
        # MFA 설정 상세 가이드 추가
        guide_steps.extend([
            {
                'type': 'info',
                'title': '📱 MFA 디바이스 유형',
                'content': '• Virtual MFA (Google Authenticator, Authy 등)\n• Hardware MFA (YubiKey 등)\n• SMS MFA (텍스트 메시지)'
            },
            {
                'type': 'step',
                'title': 'MFA 설정 절차',
                'content': '1. AWS Console 로그인\n2. 우상단 계정명 > "내 보안 자격 증명"\n3. "다중 인증(MFA)" 섹션\n4. "MFA 디바이스 할당" 클릭\n5. 디바이스 유형 선택 및 설정'
            }
        ])
        
        return {
            'title': '1.9 MFA 설정 수동 조치 가이드',
            'description': '원본 팀원이 작성한 수동 조치 절차를 따라 MFA 보안을 강화하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        # 원본: MFA 설정은 사용자의 물리적/가상 디바이스 등록이 필요하므로 자동화할 수 없음
        return [{
            'item': 'manual_mfa_setup',
            'status': 'info',
            'message': '[FIX] 1.9 MFA 설정은 사용자의 물리적/가상 디바이스 등록이 필요하므로 자동화할 수 없습니다.'
        }, {
            'item': 'root_mfa_guide',
            'status': 'info',
            'message': '  └─ [Root 계정] AWS Management Console에 Root로 로그인하여 [내 보안 자격 증명]에서 MFA 디바이스를 할당하세요.'
        }, {
            'item': 'user_mfa_guide',
            'status': 'info',
            'message': '  └─ [IAM 사용자] 다음 사용자들에게 각자 로그인하여 [내 보안 자격 증명]에서 MFA를 설정하도록 안내하세요.'
        }]