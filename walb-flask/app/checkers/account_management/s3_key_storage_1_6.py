"""
1.6 S3 키 페어 저장 체커
S3에 저장된 키 페어 파일을 점검합니다.
"""
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class S3KeyStorageChecker(BaseChecker):
    """1.6 S3 키 페어 저장 체커"""
    
    @property
    def item_code(self):
        return "1.6"
    
    @property 
    def item_name(self):
        return "S3 키 페어 저장"
    
    def run_diagnosis(self):
        """진단 실행"""
        try:
            if self.session:
                s3 = self.session.client('s3')
            else:
                s3 = self.session.client('s3')
            
            risky_key_files = []
            all_buckets = []
            key_file_stats = {'pem': 0, 'key': 0, 'ppk': 0, 'private': 0}
            
            # S3 버킷 목록 조회
            try:
                buckets_response = s3.list_buckets()
                buckets = buckets_response.get('Buckets', [])
                
                for bucket in buckets:
                    bucket_name = bucket['Name']
                    all_buckets.append(bucket_name)
                    
                    try:
                        # 버킷 내 객체 목록 조회
                        paginator = s3.get_paginator('list_objects_v2')
                        for page in paginator.paginate(Bucket=bucket_name):
                            for obj in page.get('Contents', []):
                                key = obj['Key']
                                
                                # 키 파일 확장자 검사
                                if any(key.lower().endswith(ext) for ext in ['.pem', '.key', '.ppk', 'private']):
                                    # 버킷 퍼블릭 접근 설정 확인
                                    is_public = self._check_public_access(s3, bucket_name)
                                    
                                    # 객체 퍼블릭 접근 설정 확인
                                    object_public = self._check_object_public_access(s3, bucket_name, key)
                                    
                                    risky_key_files.append({
                                        'bucket_name': bucket_name,
                                        'object_key': key,
                                        'size': obj.get('Size', 0),
                                        'last_modified': obj.get('LastModified', '').strftime('%Y-%m-%d %H:%M:%S') if obj.get('LastModified') else 'unknown',
                                        'is_bucket_public': is_public,
                                        'is_object_public': object_public,
                                        'risk_level': 'high' if (is_public or object_public) else 'medium'
                                    })
                                    
                                    # 확장자별 통계
                                    for ext in ['pem', 'key', 'ppk', 'private']:
                                        if ext in key.lower():
                                            key_file_stats[ext] += 1
                                            break
                                            
                    except ClientError as e:
                        # 개별 버킷 접근 실패 시 건너뛰기 (권한 부족 등)
                        continue
                        
            except ClientError as e:
                return {
                    'status': 'error',
                    'error_message': f'S3 버킷 목록을 조회하는 중 오류가 발생했습니다: {str(e)}'
                }
            
            # 결과 분석
            has_issues = len(risky_key_files) > 0
            risk_level = self.calculate_risk_level(len(risky_key_files))
            
            return {
                'status': 'success',
                'has_issues': has_issues,
                'risk_level': risk_level,
                'total_buckets': len(all_buckets),
                'risky_key_files': risky_key_files,
                'key_files_count': len(risky_key_files),
                'key_file_stats': key_file_stats,
                'recommendation': "S3에 키 페어 파일을 저장하지 마세요. 필요시 AWS Secrets Manager나 AWS Systems Manager Parameter Store를 사용하고, 버킷 접근을 엄격히 제한하세요."
            }
            
        except ClientError as e:
            return {
                'status': 'error',
                'error_message': f'S3 정보를 조회하는 중 오류가 발생했습니다: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f'진단 수행 중 예상치 못한 오류가 발생했습니다: {str(e)}'
            }
    
    def _check_public_access(self, s3, bucket_name):
        """버킷의 퍼블릭 접근 설정 확인"""
        try:
            # 버킷 정책 확인
            try:
                bucket_policy = s3.get_bucket_policy(Bucket=bucket_name)
                # 간단한 퍼블릭 정책 패턴 검사
                policy_text = bucket_policy.get('Policy', '')
                if '"Principal": "*"' in policy_text or '"Principal": {"AWS": "*"}' in policy_text:
                    return True
            except ClientError:
                pass
            
            # 퍼블릭 액세스 블록 설정 확인
            try:
                public_access_block = s3.get_public_access_block(Bucket=bucket_name)
                config = public_access_block.get('PublicAccessBlockConfiguration', {})
                if not all([
                    config.get('BlockPublicAcls', False),
                    config.get('IgnorePublicAcls', False),
                    config.get('BlockPublicPolicy', False),
                    config.get('RestrictPublicBuckets', False)
                ]):
                    return True
            except ClientError:
                # 설정이 없으면 잠재적으로 퍼블릭 가능
                return True
            
            return False
        except Exception:
            return True  # 확인 실패 시 위험으로 간주
    
    def _check_object_public_access(self, s3, bucket_name, object_key):
        """객체의 퍼블릭 접근 설정 확인"""
        try:
            acl_response = s3.get_object_acl(Bucket=bucket_name, Key=object_key)
            grants = acl_response.get('Grants', [])
            
            for grant in grants:
                grantee = grant.get('Grantee', {})
                if grantee.get('Type') == 'Group':
                    uri = grantee.get('URI', '')
                    if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                        return True
            return False
        except Exception:
            return False
    
    def _format_result_summary(self, result):
        """결과 요약 포맷팅"""
        if result.get('has_issues'):
            key_files_count = result.get('key_files_count', 0)
            return f"⚠️ S3에서 {key_files_count}개의 키 파일이 발견되었습니다."
        else:
            total_buckets = result.get('total_buckets', 0)
            return f"✅ {total_buckets}개 버킷에서 키 파일이 발견되지 않았습니다."
    
    def _format_result_details(self, result):
        """결과 상세 정보 포맷팅"""
        details = {
            'total_buckets': {
                'count': result.get('total_buckets', 0),
                'description': '검사한 S3 버킷 수'
            }
        }
        
        key_file_stats = result.get('key_file_stats', {})
        if any(key_file_stats.values()):
            details['key_file_statistics'] = {
                'pem_files': key_file_stats.get('pem', 0),
                'key_files': key_file_stats.get('key', 0),
                'ppk_files': key_file_stats.get('ppk', 0),
                'private_files': key_file_stats.get('private', 0),
                'description': '키 파일 유형별 통계'
            }
        
        if result.get('has_issues'):
            risky_files = result.get('risky_key_files', [])
            public_files = [f for f in risky_files if f.get('is_bucket_public') or f.get('is_object_public')]
            
            details['risky_key_files'] = {
                'count': len(risky_files),
                'public_accessible': len(public_files),
                'files': [f"{f['bucket_name']}/{f['object_key']}" for f in risky_files],
                'description': 'S3에 저장된 키 파일',
                'details': risky_files,
                'recommendation': result.get('recommendation', '')
            }
        
        return details
    
    def _get_fix_options(self, result):
        """자동 조치 옵션 반환"""
        if not result.get('has_issues'):
            return None
        
        risky_files = result.get('risky_key_files', [])
        if not risky_files:
            return None
        
        return [{
            'id': 'secure_key_files',
            'title': '키 파일 보안 조치',
            'description': f'{len(risky_files)}개의 키 파일에 대해 접근 제한을 설정합니다.',
            'items': [{'id': f"{f['bucket_name']}:{f['object_key']}", 'name': f['object_key'], 'description': f"버킷: {f['bucket_name']} | 위험도: {f['risk_level']}"} for f in risky_files],
            'action_type': 'secure_files'
        }]
    
    def _get_manual_guide(self, result):
        """수동 조치 가이드 반환 - 원본 1.6 fix() 함수 내용"""
        if not result.get('has_issues'):
            return None
        
        risky_files = result.get('risky_key_files', [])
        if not risky_files:
            return None
        
        # 원본 fix() 함수의 수동 조치 옵션들을 웹 UI로 변환
        guide_steps = [
            {
                'type': 'warning',
                'title': '[FIX] 1.6 공개된 S3 버킷의 Key Pair 파일 조치',
                'content': '공개된 버킷의 .pem 파일을 삭제하거나 버킷 자체를 비공개로 전환해야 합니다.'
            },
            {
                'type': 'step',
                'title': '옵션 1. 키 파일 삭제 (Delete Keys)',
                'content': '위험한 .pem 파일들을 S3 버킷에서 완전히 삭제합니다. 주의: 파일이 삭제되면 복구할 수 없습니다.'
            },
            {
                'type': 'step',
                'title': '옵션 2. 버킷 비공개 전환 (Privatize Bucket)',
                'content': '버킷의 모든 퍼블릭 액세스를 차단하여 외부 접근을 완전히 막습니다.'
            },
            {
                'type': 'step',
                'title': '옵션 3. 객체별 ACL 설정',
                'content': '개별 .pem 파일의 ACL을 수정하여 소유자만 접근 가능하도록 설정합니다.'
            }
        ]
        
        # 위험한 파일 목록을 버킷별로 그룹화
        bucket_groups = {}
        for file_info in risky_files:
            bucket = file_info['bucket_name']
            if bucket not in bucket_groups:
                bucket_groups[bucket] = []
            bucket_groups[bucket].append(file_info['object_key'])
        
        # CLI 명령어 추가
        cli_commands = []
        for bucket, files in bucket_groups.items():
            cli_commands.append(f"# 버킷 '{bucket}' 비공개 전환")
            cli_commands.append(f"aws s3api put-public-access-block --bucket {bucket} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true")
            cli_commands.append(f"")
            cli_commands.append(f"# '{bucket}' 키 파일들 삭제")
            for file_key in files:
                cli_commands.append(f"aws s3 rm s3://{bucket}/{file_key}")
            cli_commands.append("")
        
        if cli_commands:
            guide_steps.append({
                'type': 'commands',
                'title': 'AWS CLI 명령어 예시',
                'content': cli_commands
            })
        
        return {
            'title': '1.6 S3 Key Pair 저장소 관리 수동 조치 가이드',
            'description': '원본 팀원이 작성한 수동 조치 절차를 따라 키 파일 보안을 강화하세요.',
            'steps': guide_steps
        }
    
    def execute_fix(self, selected_items):
        """자동 조치 실행"""
        try:
            if self.session:
                s3 = self.session.client('s3')
            else:
                s3 = self.session.client('s3')
            
            results = []
            
            for fix_id, items in selected_items.items():
                if fix_id == 'secure_key_files':
                    for item in items:
                        bucket_name, object_key = item['id'].split(':', 1)
                        try:
                            # 객체에 대한 퍼블릭 접근 제거 (private ACL 설정)
                            s3.put_object_acl(
                                Bucket=bucket_name,
                                Key=object_key,
                                ACL='private'
                            )
                            
                            results.append({
                                'item': object_key,
                                'status': 'success',
                                'message': f'{bucket_name}/{object_key}의 접근 권한이 private으로 설정되었습니다.'
                            })
                            
                        except ClientError as e:
                            results.append({
                                'item': object_key,
                                'status': 'error',
                                'message': f'{object_key} 보안 설정 실패: {str(e)}'
                            })
                    
                    # 전체 요약 메시지 추가
                    results.append({
                        'item': 'summary',
                        'status': 'warning',
                        'message': f'키 파일 보안 조치가 완료되었습니다. 보안을 위해 키 파일을 S3에서 제거하고 AWS Secrets Manager 사용을 권장합니다.'
                    })
            
            return results
            
        except Exception as e:
            return [{
                'item': 'system',
                'status': 'error',
                'message': f'보안 조치 실행 중 오류가 발생했습니다: {str(e)}'
            }]