"""
[1.6] Key Pair 보관 관리 체커
공개 가능한 S3 버킷에 Key Pair(.pem) 파일이 저장되어 있는지 진단 및 조치
"""
import streamlit as st
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class KeyPairStorageChecker(BaseChecker):
    """1.6 Key Pair 보관 관리 체커"""
    
    @property
    def item_code(self):
        return "1.6"
    
    @property
    def item_name(self):
        return "Key Pair 보관 관리"
    
    def is_bucket_public(self, s3_client, bucket_name):
        """S3 버킷이 공개적으로 접근 가능한지 확인"""
        try:
            # Public Access Block 설정 확인
            pab = s3_client.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
            if all([pab.get('BlockPublicAcls'), pab.get('IgnorePublicAcls'), 
                    pab.get('BlockPublicPolicy'), pab.get('RestrictPublicBuckets')]):
                return False
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
                raise e
        
        try:
            # 버킷 정책 상태 확인
            policy_status = s3_client.get_bucket_policy_status(Bucket=bucket_name)
            if policy_status['PolicyStatus']['IsPublic']:
                return True
        except ClientError:
            pass
        
        try:
            # ACL 확인
            acl = s3_client.get_bucket_acl(Bucket=bucket_name)
            for grant in acl['Grants']:
                if grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                    return True
        except ClientError:
            pass
        
        return False
    
    def run_diagnosis(self):
        """
        진단 실행 - 공개 가능한 S3 버킷에 Key Pair(.pem) 파일이 저장되어 있는지 점검
        """
        try:
            s3 = self.session.client('s3')
            vulnerable_keys = {}
            total_buckets = 0
            public_buckets = 0
            
            # 모든 S3 버킷 조회
            buckets_response = s3.list_buckets()
            total_buckets = len(buckets_response['Buckets'])
            
            for bucket in buckets_response['Buckets']:
                bucket_name = bucket['Name']
                
                # 버킷이 공개 가능한지 확인
                if self.is_bucket_public(s3, bucket_name):
                    public_buckets += 1
                    
                    try:
                        # 페이지네이션으로 모든 객체 조회
                        paginator = s3.get_paginator('list_objects_v2')
                        pages = paginator.paginate(Bucket=bucket_name)
                        
                        for page in pages:
                            for obj in page.get('Contents', []):
                                # .pem 파일 확인
                                if obj['Key'].lower().endswith('.pem'):
                                    if bucket_name not in vulnerable_keys:
                                        vulnerable_keys[bucket_name] = []
                                    vulnerable_keys[bucket_name].append({
                                        'key': obj['Key'],
                                        'size': obj['Size'],
                                        'last_modified': obj['LastModified'],
                                        'storage_class': obj.get('StorageClass', 'STANDARD')
                                    })
                    except ClientError as e:
                        # 접근 권한이 없는 버킷은 건너뛰기
                        if e.response['Error']['Code'] not in ['AccessDenied', 'NoSuchBucket']:
                            raise e
            
            # 진단 결과 생성
            total_pem_files = sum(len(files) for files in vulnerable_keys.values())
            is_compliant = total_pem_files == 0
            risk_level = self.calculate_risk_level(total_pem_files, severity_score=3)
            
            return {
                "status": "success",
                "compliant": is_compliant,
                "risk_level": risk_level,
                "vulnerable_keys": vulnerable_keys,
                "total_buckets": total_buckets,
                "public_buckets": public_buckets,
                "total_pem_files": total_pem_files,
                "has_issues": not is_compliant,
                "message": "✅ 공개 가능한 S3 버킷에서 Key Pair 파일이 발견되지 않았습니다." if is_compliant else 
                          f"⚠️ {len(vulnerable_keys)}개의 공개 버킷에서 총 {total_pem_files}개의 Key Pair 파일(.pem)이 발견되었습니다."
            }
            
        except ClientError as e:
            return {
                "status": "error",
                "error_message": f"S3 버킷 정보를 가져오는 중 오류 발생: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error", 
                "error_message": f"예상치 못한 오류 발생: {str(e)}"
            }
    
    def execute_fix(self, selected_items):
        """
        조치 실행 - 선택된 버킷/파일에 대한 보안 조치
        """
        s3 = self.session.client('s3')
        results = []
        
        for item in selected_items:
            bucket_name = item['bucket']
            action = item['action']  # 'delete_files', 'privatize_bucket', 'ignore'
            
            try:
                if action == 'delete_files':
                    # 선택된 .pem 파일들 삭제
                    if 'files' in item and item['files']:
                        objects_to_delete = [{'Key': file_info['key']} for file_info in item['files']]
                        s3.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': objects_to_delete}
                        )
                        results.append({
                            "user": bucket_name,  # user 키로 변경 (UI 핸들러 호환성)
                            "status": "success",
                            "action": f"{len(objects_to_delete)}개의 .pem 파일 삭제 완료",
                            "deleted_files": [obj['Key'] for obj in objects_to_delete]
                        })
                    else:
                        results.append({
                            "user": bucket_name,  # user 키로 변경
                            "status": "no_action",
                            "message": "삭제할 파일이 선택되지 않았습니다."
                        })
                
                elif action == 'privatize_bucket':
                    # 버킷 퍼블릭 액세스 차단
                    s3.put_public_access_block(
                        Bucket=bucket_name,
                        PublicAccessBlockConfiguration={
                            'BlockPublicAcls': True,
                            'IgnorePublicAcls': True,
                            'BlockPublicPolicy': True,
                            'RestrictPublicBuckets': True
                        }
                    )
                    results.append({
                        "user": bucket_name,  # user 키로 변경
                        "status": "success",
                        "action": "버킷 퍼블릭 액세스 차단 완료"
                    })
                
                elif action == 'ignore':
                    results.append({
                        "user": bucket_name,  # user 키로 변경
                        "status": "no_action",
                        "message": "조치를 건너뛰었습니다."
                    })
                
            except ClientError as e:
                results.append({
                    "user": bucket_name,  # user 키로 변경
                    "status": "error",
                    "error": f"AWS API 오류: {str(e)}"
                })
            except Exception as e:
                results.append({
                    "user": bucket_name,  # user 키로 변경
                    "status": "error",
                    "error": f"예상치 못한 오류: {str(e)}"
                })
        
        return results
    
    def render_result_ui(self, result, item_key, ui_handler):
        """진단 결과 UI 렌더링"""
        if result.get('status') != 'success':
            st.error(f"❌ 진단 실패: {result.get('error_message', '알 수 없는 오류')}")
            return
        
        # 컴플라이언스 상태 표시
        if result['compliant']:
            st.success("✅ **양호**: 공개 가능한 S3 버킷에서 Key Pair 파일이 발견되지 않았습니다.")
        else:
            st.error(f"❌ **취약**: {len(result['vulnerable_keys'])}개의 공개 버킷에서 총 {result['total_pem_files']}개의 Key Pair 파일(.pem)이 발견되었습니다.")
        
        # 통계 정보
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 S3 버킷", result['total_buckets'])
        with col2:
            st.metric("공개 버킷", result['public_buckets'])
        with col3:
            st.metric("취약한 .pem 파일", result['total_pem_files'])
        with col4:
            risk_colors = {"low": "🟢", "medium": "🟡", "high": "🔴"}
            st.metric("위험도", f"{risk_colors.get(result['risk_level'], '⚪')} {result['risk_level'].upper()}")
        
        # 취약한 Key Pair 파일 상세 정보
        if result['vulnerable_keys']:
            st.subheader("🔍 공개 버킷 내 Key Pair 파일 상세")
            
            for bucket_name, files in result['vulnerable_keys'].items():
                with st.expander(f"🪣 버킷: {bucket_name} ({len(files)}개 파일)"):
                    st.warning(f"⚠️ 이 버킷은 공개적으로 접근 가능하며 {len(files)}개의 .pem 파일을 포함하고 있습니다.")
                    
                    for file_info in files:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**파일명:** `{file_info['key']}`")
                            st.write(f"**크기:** {file_info['size']:,} bytes")
                        
                        with col2:
                            st.write(f"**수정일:** {file_info['last_modified']}")
                            st.write(f"**스토리지 클래스:** {file_info['storage_class']}")
                        
                        st.divider()
        
        # 보안 권장사항
        st.subheader("🛡️ 보안 권장사항")
        st.info("""
        **Key Pair 안전한 보관 방법:**
        - 🔒 **비공개 버킷 사용**: Private S3 버킷에 저장하고 퍼블릭 액세스 완전 차단
        - 🔐 **암호화 적용**: S3 버킷에 KMS 암호화 설정 적용
        - 👥 **접근 권한 제한**: IAM 정책으로 필요한 사용자만 접근 허용
        - 📝 **정기적 점검**: 주기적으로 Key Pair 파일 위치 및 권한 검토
        - 🗂️ **별도 저장소**: EC2 콘솔(/) 디렉터리 등 공용 공간에 저장 금지
        """)
        
        # 조치 버튼 표시
        if result['vulnerable_keys']:
            if st.button("🔧 조치 실행", key=f"btn_show_fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
        
        # 조치 완료 후 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """조치 폼 UI 렌더링"""
        st.subheader("🔧 Key Pair 보관 관리 조치")
        
        if not result.get('vulnerable_keys'):
            st.info("조치할 항목이 없습니다.")
            return
        
        st.warning("⚠️ **주의**: 아래 조치는 S3 버킷과 파일에 직접적인 영향을 미칩니다. 신중하게 선택하세요.")
        
        selected_actions = []
        
        for bucket_name, files in result['vulnerable_keys'].items():
            st.subheader(f"🪣 버킷: {bucket_name}")
            
            action = st.radio(
                f"버킷 '{bucket_name}'에 대한 조치 선택:",
                ["ignore", "delete_files", "privatize_bucket"],
                format_func=lambda x: {
                    "ignore": "❌ 조치 건너뛰기",
                    "delete_files": "🗑️ .pem 파일 삭제",
                    "privatize_bucket": "🔒 버킷 퍼블릭 액세스 차단"
                }[x],
                key=f"action_{bucket_name}_{item_key}"
            )
            
            if action == "delete_files":
                st.write("삭제할 파일을 선택하세요:")
                selected_files = []
                
                for i, file_info in enumerate(files):
                    if st.checkbox(
                        f"📄 {file_info['key']} ({file_info['size']:,} bytes)",
                        key=f"file_{bucket_name}_{i}_{item_key}"
                    ):
                        selected_files.append(file_info)
                
                if selected_files:
                    st.warning(f"⚠️ 선택된 {len(selected_files)}개 파일이 영구적으로 삭제됩니다.")
                
                selected_actions.append({
                    "bucket": bucket_name,
                    "action": action,
                    "files": selected_files
                })
                
            elif action == "privatize_bucket":
                st.warning("⚠️ 이 버킷의 모든 퍼블릭 액세스가 차단됩니다.")
                selected_actions.append({
                    "bucket": bucket_name,
                    "action": action
                })
            
            else:  # ignore
                selected_actions.append({
                    "bucket": bucket_name,
                    "action": action
                })
            
            st.divider()
        
        # 조치 실행 버튼
        if st.button("🚀 선택된 조치 실행", key=f"execute_fix_{item_key}", type="primary"):
            if any(action['action'] != 'ignore' for action in selected_actions):
                ui_handler.execute_fix(selected_actions, item_key, self.item_code)
            else:
                st.info("선택된 조치가 없습니다.")