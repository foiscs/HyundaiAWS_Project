"""
1.6 S3 Key Pair 저장 관리 진단 (Flask용)
mainHub의 s3_key_pair_storage_1_6.py를 Streamlit 종속성 제거하여 이식
"""
import boto3
from ..base_checker import BaseChecker
from botocore.exceptions import ClientError

class KeyPairStorageChecker(BaseChecker):
    """1.6 S3 Key Pair 저장 관리 진단"""
    
    @property
    def item_code(self):
        return "1.6"
    
    @property 
    def item_name(self):
        return "S3 Key Pair 저장 관리"
    
    def run_diagnosis(self):
        """
        진단 수행 - S3 버킷에 Key Pair 파일이 저장되어 있는지 점검
        """
        try:
            if self.session:
                s3 = self.session.client('s3')
            else:
                s3 = boto3.client('s3')
            
            suspicious_files = []
            total_buckets = 0
            
            # 모든 버킷 조회
            buckets = s3.list_buckets()
            
            for bucket in buckets['Buckets']:
                total_buckets += 1
                bucket_name = bucket['Name']
                
                try:
                    # 버킷 내 객체 조회
                    paginator = s3.get_paginator('list_objects_v2')
                    pages = paginator.paginate(Bucket=bucket_name)
                    
                    for page in pages:
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                key = obj['Key']
                                # Key Pair 파일 패턴 검사
                                if (key.endswith('.pem') or key.endswith('.ppk') or 
                                    'key' in key.lower() or 'keypair' in key.lower()):
                                    suspicious_files.append({
                                        'bucket': bucket_name,
                                        'key': key,
                                        'size': obj['Size'],
                                        'last_modified': obj['LastModified'].isoformat()
                                    })
                                    
                except ClientError as e:
                    # 접근 권한이 없는 버킷은 스킵
                    if e.response['Error']['Code'] not in ['AccessDenied', 'NoSuchBucket']:
                        raise e
            
            # 위험도 계산
            issues_count = len(suspicious_files)
            risk_level = self.calculate_risk_level(
                issues_count,
                3  # Key Pair 파일 노출은 높은 위험도
            )
            
            return {
                "status": "success",
                "suspicious_files": suspicious_files,
                "total_buckets": total_buckets,
                "issues_count": issues_count,
                "risk_level": risk_level,
                "has_issues": issues_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        total_buckets = result.get('total_buckets', 0)
        issues_count = result.get('issues_count', 0)
        
        if issues_count > 0:
            return f"⚠️ {total_buckets}개 S3 버킷에서 {issues_count}개의 의심스러운 Key Pair 파일이 발견되었습니다."
        else:
            return f"✅ {total_buckets}개 S3 버킷에서 Key Pair 파일이 발견되지 않았습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            "S3 스캔 결과": {
                "검사한 버킷 수": result.get('total_buckets', 0),
                "의심스러운 파일": result.get('issues_count', 0),
                "recommendation": "Key Pair 파일은 S3에 저장하지 말고 안전한 Key 관리 서비스를 사용하세요."
            }
        }
        
        if result.get('suspicious_files'):
            details["의심스러운 파일 목록"] = {}
            for file_info in result['suspicious_files']:
                file_key = f"{file_info['bucket']}/{file_info['key']}"
                details["의심스러운 파일 목록"][file_key] = {
                    "size": file_info['size'],
                    "last_modified": file_info['last_modified']
                }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        suspicious_files = result.get('suspicious_files', [])
        
        if suspicious_files:
            return [{
                "type": "delete_keypair_files",
                "title": "Key Pair 파일 삭제",
                "description": f"{len(suspicious_files)}개의 의심스러운 Key Pair 파일을 삭제합니다.",
                "items": [{"bucket": f['bucket'], "key": f['key'], "action": "파일 삭제"} 
                         for f in suspicious_files],
                "severity": "high",
                "warning": "주의: 파일 삭제는 되돌릴 수 없습니다. 중요한 파일인지 확인하세요."
            }]
        
        return None
    
    def execute_fix(self, selected_items):
        """조치 실행"""
        try:
            if self.session:
                s3 = self.session.client('s3')
            else:
                s3 = boto3.client('s3')
            
            results = []
            files_to_delete = selected_items.get('suspicious_files', [])
            
            for file_info in files_to_delete:
                try:
                    s3.delete_object(
                        Bucket=file_info['bucket'],
                        Key=file_info['key']
                    )
                    results.append({
                        "file": f"{file_info['bucket']}/{file_info['key']}",
                        "action": "파일 삭제",
                        "status": "success"
                    })
                except ClientError as e:
                    results.append({
                        "file": f"{file_info['bucket']}/{file_info['key']}",
                        "action": "파일 삭제",
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "file": "전체",
                "action": "파일 삭제",
                "status": "error",
                "error": str(e)
            }]