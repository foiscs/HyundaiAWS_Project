#!/usr/bin/env python3
"""
모니터링 서비스 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'walb-flask'))

from app import create_app
import json

app = create_app()
with app.app_context():
    from app.models.account import AWSAccount
    from app.services.monitoring_service import MonitoringService
    
    accounts = AWSAccount.load_all()
    if accounts:
        test_account = accounts[0]
        print(f'Testing account: {test_account.account_id} ({test_account.cloud_name})')
        print(f'Connection type: {test_account.connection_type}')
        print(f'Region: {test_account.primary_region}')
        
        monitoring_service = MonitoringService()
        try:
            print('\n=== Testing AWS session creation ===')
            session = monitoring_service.create_aws_session(test_account)
            print('Session created successfully')
            
            print('\n=== Testing CloudWatch status ===')
            cloudwatch_status = monitoring_service.check_cloudwatch_status(test_account)
            print(f'CloudWatch active: {cloudwatch_status.get("active", False)}')
            if 'error' in cloudwatch_status:
                print(f'CloudWatch error: {cloudwatch_status["error"]}')
            
            print('\n=== Testing CloudTrail status ===')
            cloudtrail_status = monitoring_service.check_cloudtrail_status(test_account)
            print(f'CloudTrail active: {cloudtrail_status.get("active", False)}')
            if 'error' in cloudtrail_status:
                print(f'CloudTrail error: {cloudtrail_status["error"]}')
            
            print('\n=== Testing GuardDuty status ===')
            guardduty_status = monitoring_service.check_guardduty_status(test_account)
            print(f'GuardDuty active: {guardduty_status.get("active", False)}')
            if 'error' in guardduty_status:
                print(f'GuardDuty error: {guardduty_status["error"]}')
            
            print('\n=== Testing Comprehensive Status ===')
            comprehensive_status = monitoring_service.get_comprehensive_monitoring_status(test_account)
            print(f'Overall health: {comprehensive_status.get("overall_health", "unknown")}')
            print(f'Services status:')
            for service_name, service_data in comprehensive_status.get('services', {}).items():
                print(f'  - {service_name}: {"OK" if service_data.get("active") else "FAIL"} active')
                if 'error' in service_data:
                    print(f'    Error: {service_data["error"]}')
            
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
    else:
        print('No accounts found')