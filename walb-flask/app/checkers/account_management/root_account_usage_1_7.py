"""
1.7 루트 계정 사용 체커
AWS 루트 계정의 사용 현황을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone, timedelta
from ..base_checker import BaseChecker

class RootAccountUsageChecker(BaseChecker):
    """1.7 루트 계정 사용 체커"""
    
    @property
    def item_code(self):
        return "1.7"
    
    @property 
    def item_name(self):
        return "루트 계정 사용"
    
    def run_diagnosis(self):
        """진단 실행 - 원본 1.7 로직 그대로 구현"""
        try:
            if self.session:
                cloudtrail = self.session.client('cloudtrail')
            else:
                cloudtrail = self.session.client('cloudtrail')
            
            # 원본 로직: 최근 90일 간 Root 계정 활동 내역 조회
            lookback_days = 90
            now = datetime.now(timezone.utc)
            start_time = now - timedelta(days=lookback_days)
            
            root_events = set()  # 중복 제거를 위해 set 사용
            
            try:
                # Root 계정이 수행한 이벤트 목록 수집
                paginator = cloudtrail.get_paginator('lookup_events')
                pages = paginator.paginate(
                    LookupAttributes=[
                        {'AttributeKey': 'Username', 'AttributeValue': 'Root'}
                    ],
                    StartTime=start_time,
                    EndTime=now
                )
                
                for page in pages:
                    for event in page['Events']:
                        try:
                            import json
                            cloudtrail_event = json.loads(event['CloudTrailEvent'])  
                            user_type = cloudtrail_event.get('userIdentity', {}).get('type', '')
                            if user_type == 'Root':
                                event_name = cloudtrail_event.get('eventName')
                                if event_name:
                                    root_events.add(event_name)
                        except Exception:
                            continue 
                
            except ClientError as e:
                return {
                    'status': 'error',
                    'error_message': f'CloudTrail 이벤트 조회 중 오류 발생: {str(e)}'
                }
            
            # 결과 분석 (원본 로직)
            has_issues = len(root_events) > 0  # 이벤트가 있으면 수동 검토 필요
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': 'medium' if has_issues else 'low',
                'lookback_days': lookback_days,
                'root_events': sorted(list(root_events)),
                'events_count': len(root_events),
                'recommendation': "[ⓘ MANUAL] 이 항목은 루트 계정이 서비스 용도로 사용되는지 여부를 수동으로 판별해야 합니다."
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'루트 계정 정보를 조회하는 중 오류가 발생했습니다: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        events_count = result.get('events_count', 0)
        root_events = result.get('root_events', [])
        
        if events_count > 0:
            summary = f"[⚠ 참고] 최근 루트 계정으로 수행된 서비스 이벤트 {events_count}건:"
            for event in root_events:
                summary += f"\n  ├─ {event}"
            summary += f"\n\n[수동 판정 필요]"
            summary += f"\n  └─ 위 이벤트 중 운영성 또는 서비스성 작업(예: RunInstances, PutObject 등)이 있다면 '서비스 용도 사용'으로 판단하세요."
            return summary
        else:
            return "[✓ COMPLIANT] 최근 루트 계정으로 수행된 서비스 관련 이벤트가 없습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'lookback_period': {
                'days': result.get('lookback_days', 90),
                'description': '조회 기간 (일)'
            },
            'events_found': {
                'count': result.get('events_count', 0),
                'description': '발견된 루트 계정 이벤트 수'
            }
        }
        
        if result.get('events_count', 0) > 0:
            root_events = result.get('root_events', [])
            details['root_events'] = {
                'count': len(root_events),
                'events': root_events,
                'description': '루트 계정으로 수행된 이벤트 목록',
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        # 원본 1.7은 fix() 함수가 있지만 수동 조치만 제공
        return None
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 1.7 fix() 함수 내용"""
        if not result.get('has_issues'):
            return None
        
        # 원본 fix() 함수의 내용을 그대로 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 1.7 루트 Access Key 조치 가이드',
                'content': '루트 Access Key가 존재하는 경우, 자동 조치 대신 상세하고 안전한 수동 조치 가이드를 제공합니다.'
            },
            {
                'type': 'step',
                'title': '1. AWS Management Console 로그인',
                'content': '루트 계정으로 AWS Management Console에 로그인합니다.'
            },
            {
                'type': 'step',
                'title': '2. 보안 자격 증명 페이지 이동',
                'content': "우측 상단 계정명 클릭 > '보안 자격 증명' > 'Access Key'로 이동합니다."
            },
            {
                'type': 'step',
                'title': '3. Access Key 비활성화/삭제',
                'content': "사용 중인 Access Key가 있다면 즉시 '비활성화'하거나, 가능하면 완전히 삭제합니다."
            },
            {
                'type': 'step',
                'title': '4. MFA 설정 확인',
                'content': '루트 계정에 MFA가 적용되어 있는지 추가로 확인합니다.'
            },
            {
                'type': 'info',
                'title': '💡 보안 권장사항',
                'content': '루트 계정은 계정 관리 용도로만 제한적으로 사용하고, 서비스 운영에는 개별 IAM 사용자를 활용하세요.'
            }
        ]
        
        # 수동 검토가 필요한 이벤트가 있는 경우
        if result.get('events_count', 0) > 0:
            root_events = result.get('root_events', [])
            guide_steps.append({
                'type': 'info',
                'title': '[ⓘ MANUAL] 수동 판정 필요',
                'content': f'최근 루트 계정으로 수행된 {len(root_events)}개 이벤트 중 운영성 또는 서비스성 작업(예: RunInstances, PutObject 등)이 있다면 "서비스 용도 사용"으로 판단하세요.'
            })
        
        return {
            'title': '1.7 루트 계정 사용 관리 수동 조치 가이드',
            'description': '원본 팀원이 작성한 수동 조치 절차를 따라 루트 계정 보안을 강화하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        # 원본 1.7은 fix() 함수가 없음 - 수동 점검만 제공
        return [{
            'item': 'manual_review_only',
            'status': 'info',
            'message': '[ⓘ MANUAL] 이 항목은 루트 계정이 서비스 용도로 사용되는지 여부를 수동으로 판별해야 합니다.'
        }, {
            'item': 'review_guidance',
            'status': 'info',
            'message': '위 이벤트 중 운영성 또는 서비스성 작업(예: RunInstances, PutObject 등)이 있다면 "서비스 용도 사용"으로 판단하세요.'
        }]
