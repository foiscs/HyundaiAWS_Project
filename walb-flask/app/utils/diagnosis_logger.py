"""
진단 로그 관리 유틸리티
진단 실행 시 전체 로그를 파일로 저장하고 관리
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class DiagnosisLogger:
    """진단 로그 관리 클래스"""
    
    def __init__(self, log_dir: str = "logs/diagnosis"):
        """
        진단 로거 초기화
        
        Args:
            log_dir (str): 로그 파일을 저장할 디렉토리 경로
        """
        self.log_dir = log_dir
        self.current_session_id = None
        self.session_logger = None
        self.session_log_file = None
        
        # 로그 디렉토리 생성
        os.makedirs(self.log_dir, exist_ok=True)
    
    def start_session(self, account_id: str, account_name: str = None, session_type: str = "batch") -> str:
        """
        새로운 진단 세션 시작
        
        Args:
            account_id (str): AWS 계정 ID
            account_name (str): AWS 계정명 (옵션)
            session_type (str): 세션 타입 (batch, single)
            
        Returns:
            str: 세션 ID
        """
        # 타임스탬프와 계정 ID로 세션 ID 및 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = f"{timestamp}_{account_id}_{session_type}"
        
        # 로그 파일 경로 설정 (타임스탬프_계정ID.log 형식)
        log_filename = f"{timestamp}_{account_id}.log"
        self.session_log_file = os.path.join(self.log_dir, log_filename)
        
        # 세션별 로거 설정
        self.session_logger = logging.getLogger(f"diagnosis_session_{self.current_session_id}")
        self.session_logger.setLevel(logging.DEBUG)
        
        # 기존 핸들러 제거
        for handler in self.session_logger.handlers[:]:
            self.session_logger.removeHandler(handler)
        
        # 파일 핸들러 추가
        file_handler = logging.FileHandler(self.session_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 로그 포맷 설정
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.session_logger.addHandler(file_handler)
        
        # 세션 시작 로그
        self.session_logger.info("="*80)
        self.session_logger.info(f"SK Shieldus AWS 보안 진단 세션 시작")
        self.session_logger.info(f"세션 ID: {self.current_session_id}")
        self.session_logger.info(f"계정 ID: {account_id}")
        if account_name:
            self.session_logger.info(f"계정명: {account_name}")
        self.session_logger.info(f"세션 타입: {session_type}")
        self.session_logger.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.session_logger.info("="*80)
        
        return self.current_session_id
    
    def log_diagnosis_start(self, item_code: str, item_name: str):
        """진단 항목 시작 로그"""
        if self.session_logger:
            self.session_logger.info(f"")
            self.session_logger.info(f"[{item_code}] {item_name} 진단 시작")
            self.session_logger.info("-" * 60)
    
    def log_diagnosis_result(self, item_code: str, item_name: str, result: Dict[str, Any]):
        """진단 결과 로그"""
        if not self.session_logger:
            return
            
        self.session_logger.info(f"[{item_code}] {item_name} 진단 완료")
        
        if result['status'] == 'success':
            self.session_logger.info(f"상태: 성공")
            self.session_logger.info(f"이슈 발견: {'있음' if result.get('result', {}).get('has_issues', False) else '없음'}")
            
            if result.get('result', {}).get('has_issues'):
                risk_level = result.get('result', {}).get('risk_level', 'unknown')
                self.session_logger.warning(f"위험도: {risk_level}")
                
                # 상세 결과 로그
                details = result.get('result', {}).get('details', {})
                if details:
                    self.session_logger.info("상세 결과:")
                    for key, value in details.items():
                        if isinstance(value, (dict, list)):
                            self.session_logger.info(f"  {key}: {json.dumps(value, ensure_ascii=False, indent=2)}")
                        else:
                            self.session_logger.info(f"  {key}: {value}")
            else:
                self.session_logger.info("✅ 보안 이슈 없음")
        else:
            self.session_logger.error(f"상태: 실패")
            error_msg = result.get('message', '알 수 없는 오류')
            self.session_logger.error(f"오류 메시지: {error_msg}")
        
        self.session_logger.info("-" * 60)
    
    def log_fix_start(self, item_code: str, item_name: str, selected_items: Dict[str, Any]):
        """자동 조치 시작 로그"""
        if self.session_logger:
            self.session_logger.info(f"")
            self.session_logger.info(f"[{item_code}] {item_name} 자동 조치 시작")
            self.session_logger.info(f"선택된 항목: {json.dumps(selected_items, ensure_ascii=False, indent=2)}")
            self.session_logger.info("-" * 60)
    
    def log_fix_result(self, item_code: str, item_name: str, result: Dict[str, Any]):
        """자동 조치 결과 로그"""
        if not self.session_logger:
            return
            
        self.session_logger.info(f"[{item_code}] {item_name} 자동 조치 완료")
        
        if result.get('status') == 'success':
            self.session_logger.info("조치 상태: 성공")
            results = result.get('results', [])
            if results:
                self.session_logger.info(f"조치된 항목 수: {len(results)}")
                for idx, res in enumerate(results, 1):
                    status = res.get('status', 'unknown')
                    message = res.get('message', '')
                    self.session_logger.info(f"  {idx}. {status}: {message}")
        else:
            self.session_logger.error("조치 상태: 실패")
            error_msg = result.get('message', '알 수 없는 오류')
            self.session_logger.error(f"오류 메시지: {error_msg}")
        
        self.session_logger.info("-" * 60)
    
    def log_session_summary(self, total_items: int, success_count: int, failed_count: int):
        """세션 요약 로그"""
        if not self.session_logger:
            return
            
        self.session_logger.info("")
        self.session_logger.info("="*80)
        self.session_logger.info("진단 세션 요약")
        self.session_logger.info("="*80)
        self.session_logger.info(f"전체 진단 항목: {total_items}개")
        self.session_logger.info(f"성공: {success_count}개")
        self.session_logger.info(f"실패: {failed_count}개")
        self.session_logger.info(f"성공률: {(success_count/total_items*100):.1f}%")
        self.session_logger.info(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.session_logger.info("="*80)
    
    def end_session(self):
        """진단 세션 종료"""
        if self.session_logger:
            # 핸들러 정리
            for handler in self.session_logger.handlers[:]:
                handler.close()
                self.session_logger.removeHandler(handler)
        
        self.current_session_id = None
        self.session_logger = None
        self.session_log_file = None
    
    def get_session_log_path(self) -> Optional[str]:
        """현재 세션의 로그 파일 경로 반환"""
        return self.session_log_file
    
    def get_recent_logs(self, limit: int = 10) -> list:
        """최근 로그 파일 목록 반환"""
        try:
            log_files = []
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(self.log_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    log_files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'modified_time': datetime.fromtimestamp(mtime),
                        'size': os.path.getsize(filepath)
                    })
            
            # 수정 시간 기준으로 정렬 (최신순)
            log_files.sort(key=lambda x: x['modified_time'], reverse=True)
            return log_files[:limit]
        
        except Exception as e:
            return []
    
    def cleanup_old_logs(self, keep_days: int = 30):
        """오래된 로그 파일 정리"""
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(self.log_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        
        except Exception as e:
            pass

# 전역 로거 인스턴스
diagnosis_logger = DiagnosisLogger()