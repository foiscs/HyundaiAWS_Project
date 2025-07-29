"""
Splunk 연동 서비스
계정별 로그 조회 및 Splunk 웹으로 리다이렉션 기능
"""

import os
import urllib.parse
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SplunkService:
    """Splunk 연동 및 쿼리 관리"""
    
    def __init__(self, splunk_web_url: str = "http://localhost:8000"):
        self.splunk_web_url = splunk_web_url
        self.log_base_path = "/var/log/splunk"
        
    def generate_splunk_search_url(self, account_id: str, log_type: str = "cloudtrail", 
                                 search_term: str = "*", earliest_time: str = "-24h") -> str:
        """계정별 Splunk 검색 URL 생성"""
        
        # 로그 파일 경로 구성
        log_file_path = f"{self.log_base_path}/{account_id}/{log_type}.log"
        
        # 기본 검색 쿼리
        if search_term == "*":
            search_query = f'index=* source="{log_file_path}"'
        else:
            search_query = f'index=* source="{log_file_path}" {search_term}'
            
        # URL 파라미터 구성
        params = {
            'q': search_query,
            'earliest': earliest_time,
            'latest': 'now'
        }
        
        # URL 인코딩
        query_string = urllib.parse.urlencode(params)
        
        # Splunk 검색 URL 생성 
        search_url = f"{self.splunk_web_url}/en-US/app/search/search?{query_string}"
        
        logger.info(f"Generated Splunk URL for account {account_id}: {search_url}")
        return search_url
    
    def get_all_log_types(self, account_id: str) -> List[str]:
        """계정의 사용 가능한 로그 타입 조회"""
        log_types = []
        account_log_dir = os.path.join(self.log_base_path, account_id)
        
        if os.path.exists(account_log_dir):
            try:
                for file in os.listdir(account_log_dir):
                    if file.endswith('.log'):
                        log_type = file.replace('.log', '')
                        log_types.append(log_type)
            except OSError as e:
                logger.error(f"Error listing log files for account {account_id}: {e}")
                
        return log_types
    
    def check_log_availability(self, account_id: str, log_type: str = "cloudtrail") -> Dict[str, Any]:
        """로그 파일 가용성 확인"""
        log_file_path = os.path.join(self.log_base_path, account_id, f"{log_type}.log")
        
        availability = {
            "account_id": account_id,
            "log_type": log_type,
            "file_path": log_file_path,
            "exists": False,
            "readable": False,
            "size": 0,
            "last_modified": None,
            "error": None
        }
        
        try:
            if os.path.exists(log_file_path):
                availability["exists"] = True
                availability["readable"] = os.access(log_file_path, os.R_OK)
                
                stat_info = os.stat(log_file_path)
                availability["size"] = stat_info.st_size
                availability["last_modified"] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
        except Exception as e:
            availability["error"] = str(e)
            logger.error(f"Error checking log availability: {e}")
            
        return availability
    
    def get_splunk_dashboard_urls(self, account_id: str) -> Dict[str, str]:
        """계정별 다양한 Splunk 대시보드 URL 반환"""
        urls = {}
        
        # 기본 로그 타입별 URL
        log_types = ["cloudtrail", "guardduty", "security-hub"]
        
        for log_type in log_types:
            urls[log_type] = self.generate_splunk_search_url(
                account_id=account_id,
                log_type=log_type,
                search_term="*",
                earliest_time="-24h"
            )
        
        # 통합 대시보드 (모든 로그)
        all_logs_query = f'index=* source="/var/log/splunk/{account_id}/*.log"'
        all_logs_params = {
            'q': all_logs_query,
            'earliest': '-24h',
            'latest': 'now'
        }
        urls["all_logs"] = f"{self.splunk_web_url}/en-US/app/search/search?{urllib.parse.urlencode(all_logs_params)}"
        
        # 보안 이벤트 필터링
        security_query = f'index=* source="/var/log/splunk/{account_id}/*.log" (severity=HIGH OR severity=CRITICAL OR eventName=ConsoleLogin OR eventName=AssumeRole)'
        security_params = {
            'q': security_query,
            'earliest': '-24h',
            'latest': 'now'
        }
        urls["security_events"] = f"{self.splunk_web_url}/en-US/app/search/search?{urllib.parse.urlencode(security_params)}"
        
        return urls
    
    def create_custom_search_url(self, account_id: str, custom_query: str, 
                                time_range: str = "-24h") -> str:
        """커스텀 검색 쿼리 URL 생성"""
        base_query = f'index=* source="/var/log/splunk/{account_id}/*.log"'
        
        if custom_query:
            full_query = f"{base_query} {custom_query}"
        else:
            full_query = base_query
            
        params = {
            'q': full_query,
            'earliest': time_range,
            'latest': 'now'
        }
        
        return f"{self.splunk_web_url}/en-US/app/search/search?{urllib.parse.urlencode(params)}"
    
    def get_account_monitoring_status(self, account_id: str) -> Dict[str, Any]:
        """계정 모니터링 상태 요약"""
        status = {
            "account_id": account_id,
            "monitoring_active": False,
            "available_logs": [],
            "log_files_status": {},
            "splunk_urls": {},
            "last_activity": None,
            "total_log_size": 0
        }
        
        # 로그 디렉토리 확인
        account_log_dir = os.path.join(self.log_base_path, account_id)
        
        if os.path.exists(account_log_dir):
            status["monitoring_active"] = True
            
            # 각 로그 파일 상태 확인
            for log_type in ["cloudtrail", "guardduty", "security-hub"]:
                log_availability = self.check_log_availability(account_id, log_type)
                
                if log_availability["exists"]:
                    status["available_logs"].append(log_type)
                    status["total_log_size"] += log_availability["size"]
                    
                    # 최근 활동 시간 추적
                    if log_availability["last_modified"]:
                        mod_time = datetime.fromisoformat(log_availability["last_modified"])
                        if not status["last_activity"] or mod_time > datetime.fromisoformat(status["last_activity"]):
                            status["last_activity"] = log_availability["last_modified"]
                
                status["log_files_status"][log_type] = log_availability
            
            # Splunk URL 생성
            status["splunk_urls"] = self.get_splunk_dashboard_urls(account_id)
        
        return status