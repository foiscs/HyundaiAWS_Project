"""
[1.5] Key Pair 접근 관리 체커
EC2 인스턴스가 Key Pair를 통해 안전하게 접근 가능한지 진단 및 조치
"""
import streamlit as st
import boto3
from botocore.exceptions import ClientError
from ..base_checker import BaseChecker

class KeyPairAccessChecker(BaseChecker):
    """1.5 Key Pair 접근 관리 체커"""
    
    @property
    def item_code(self):
        return "1.5"
    
    @property
    def item_name(self):
        return "Key Pair 접근 관리"
    
    def run_diagnosis(self):
        """
        진단 실행 - 실행 중인 모든 EC2 인스턴스에 Key Pair가 할당되어 있는지 점검
        """
        try:
            ec2 = self.session.client('ec2')
            instances_without_keypair = []
            
            # 실행 중인 인스턴스만 조회
            paginator = ec2.get_paginator('describe_instances')
            pages = paginator.paginate(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )
            
            for page in pages:
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        if 'KeyName' not in instance:
                            instances_without_keypair.append({
                                'instance_id': instance['InstanceId'],
                                'instance_type': instance.get('InstanceType', 'Unknown'),
                                'launch_time': instance.get('LaunchTime'),
                                'public_ip': instance.get('PublicIpAddress', 'N/A'),
                                'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                                'vpc_id': instance.get('VpcId', 'N/A'),
                                'subnet_id': instance.get('SubnetId', 'N/A'),
                                'security_groups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])]
                            })
            
            # 진단 결과 생성
            is_compliant = len(instances_without_keypair) == 0
            risk_level = self.calculate_risk_level(len(instances_without_keypair), severity_score=2)
            
            return {
                "status": "success",
                "compliant": is_compliant,
                "risk_level": risk_level,
                "instances_without_keypair": instances_without_keypair,
                "total_instances_checked": sum(1 for page in pages for reservation in page['Reservations'] for instance in reservation['Instances']),
                "issues_count": len(instances_without_keypair),
                "has_issues": not is_compliant,
                "message": "✅ 모든 실행 중인 EC2 인스턴스에 Key Pair가 할당되어 있습니다." if is_compliant else 
                          f"⚠️ {len(instances_without_keypair)}개의 인스턴스에 Key Pair가 할당되지 않았습니다."
            }
            
        except ClientError as e:
            return {
                "status": "error",
                "error_message": f"EC2 인스턴스 정보를 가져오는 중 오류 발생: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error", 
                "error_message": f"예상치 못한 오류 발생: {str(e)}"
            }
    
    def execute_fix(self, selected_items):
        """
        조치 실행 - Key Pair는 직접 할당이 불가능하므로 수동 조치 안내만 제공
        """
        results = []
        
        for instance in selected_items:
            # Key Pair 할당은 자동화할 수 없으므로 안내 메시지만 제공
            results.append({
                "user": instance['instance_id'],
                "status": "manual_action_required",
                "message": "수동 조치 필요: Key Pair 할당은 자동화할 수 없습니다.",
                "manual_steps": [
                    "방법 1: SSH로 접속하여 ~/.ssh/authorized_keys 파일에 새 key pair의 public key 추가",
                    "방법 2: 인스턴스의 AMI 이미지를 생성하고 새로운 인스턴스를 Key Pair와 함께 생성"
                ]
            })
        
        return results
    
    def render_result_ui(self, result, item_key, ui_handler):
        """진단 결과 UI 렌더링"""
        if result.get('status') != 'success':
            st.error(f"❌ 진단 실패: {result.get('error_message', '알 수 없는 오류')}")
            return
        
        # 컴플라이언스 상태 표시
        if result['compliant']:
            st.success("✅ **양호**: 모든 실행 중인 EC2 인스턴스에 Key Pair가 할당되어 있습니다.")
        else:
            st.error(f"❌ **취약**: {result['issues_count']}개의 인스턴스에 Key Pair가 할당되지 않았습니다.")
        
        # 통계 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 실행 중 인스턴스", result['total_instances_checked'])
        with col2:
            st.metric("Key Pair 미할당", result['issues_count'])
        with col3:
            risk_colors = {"low": "🟢", "medium": "🟡", "high": "🔴"}
            st.metric("위험도", f"{risk_colors.get(result['risk_level'], '⚪')} {result['risk_level'].upper()}")
        
        # Key Pair 미할당 인스턴스 상세 정보
        if result['instances_without_keypair']:
            st.subheader("🔍 Key Pair 미할당 인스턴스 상세")
            
            for instance in result['instances_without_keypair']:
                with st.expander(f"📟 {instance['instance_id']} - {instance['instance_type']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**퍼블릭 IP:** {instance['public_ip']}")
                        st.write(f"**프라이빗 IP:** {instance['private_ip']}")
                        st.write(f"**VPC ID:** {instance['vpc_id']}")
                    
                    with col2:
                        st.write(f"**서브넷 ID:** {instance['subnet_id']}")
                        st.write(f"**시작 시간:** {instance['launch_time']}")
                        st.write(f"**보안 그룹:** {', '.join(instance['security_groups'])}")
                    
                    st.warning("⚠️ 이 인스턴스는 Key Pair 없이 실행 중입니다.")
        
        # 보안 권장사항
        st.subheader("🛡️ 보안 권장사항")
        st.info("""
        **Key Pair 사용의 중요성:**
        - 🔐 **암호화된 접근**: 2048비트 SSH-2 RSA 키를 통한 안전한 인스턴스 접근
        - 🚫 **패스워드 제거**: 일반 패스워드 로그인 차단으로 보안 강화
        - 🎯 **접근 제어**: 개인 키 소유자만 인스턴스 접근 가능
        - 📝 **감사 추적**: Key Pair 기반 접근으로 더 나은 로그 추적
        """)
        
        # 조치 버튼 표시
        if result['instances_without_keypair']:
            if st.button("🔧 수동 조치 안내 보기", key=f"btn_show_fix_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = True
                st.rerun()
        
        # 조치 완료 후 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """조치 폼 UI 렌더링"""
        st.subheader("🔧 Key Pair 조치 안내")
        
        if not result.get('instances_without_keypair'):
            st.info("조치할 인스턴스가 없습니다.")
            return
        
        st.warning("""
        ⚠️ **중요**: Key Pair는 실행 중인 인스턴스에 직접 할당할 수 없습니다.
        아래의 수동 절차를 따라 조치해주세요.
        """)
        
        # 조치 방법 안내
        tab1, tab2 = st.tabs(["🔑 방법 1: authorized_keys 수정", "🖼️ 방법 2: AMI 재배포"])
        
        with tab1:
            st.markdown("""
            ### 실행 중인 인스턴스에 Key Pair 추가하기
            
            **준비사항:**
            - 새로운 Key Pair 생성 또는 기존 Key Pair의 public key
            - 인스턴스에 접근할 수 있는 방법 (다른 Key Pair, EC2 Instance Connect 등)
            
            **단계:**
            1. **Key Pair 생성 (필요시)**
               ```bash
               # AWS CLI로 새 Key Pair 생성
               aws ec2 create-key-pair --key-name my-new-keypair --query 'KeyMaterial' --output text > my-new-keypair.pem
               chmod 400 my-new-keypair.pem
               ```
            
            2. **인스턴스에 SSH 접속**
               ```bash
               # 기존 방법으로 접속 (예: EC2 Instance Connect)
               ssh -i existing-key.pem ec2-user@<instance-ip>
               ```
            
            3. **authorized_keys 파일 수정**
               ```bash
               # public key를 authorized_keys에 추가
               echo "ssh-rsa AAAAB3NzaC1yc2E... your-new-public-key" >> ~/.ssh/authorized_keys
               chmod 600 ~/.ssh/authorized_keys
               ```
            
            4. **연결 테스트**
               ```bash
               # 새 Key Pair로 접속 테스트
               ssh -i my-new-keypair.pem ec2-user@<instance-ip>
               ```
            """)
        
        with tab2:
            st.markdown("""
            ### AMI 이미지로 새 인스턴스 생성하기
            
            **단계:**
            1. **현재 인스턴스의 AMI 이미지 생성**
               - EC2 콘솔에서 인스턴스 선택
               - Actions → Image and templates → Create image
            
            2. **새 인스턴스 시작**
               - 생성된 AMI로 새 인스턴스 시작
               - Key Pair 선택 단계에서 원하는 Key Pair 지정
            
            3. **기존 인스턴스 대체**
               - 새 인스턴스 정상 동작 확인
               - Elastic IP 재할당 (필요시)
               - 기존 인스턴스 종료
            
            **장점:**
            - Key Pair가 확실히 할당됨
            - 깨끗한 새 환경
            
            **단점:**
            - 서비스 중단 시간 발생
            - IP 주소 변경 가능성
            """)
        
        # 대상 인스턴스 선택
        st.subheader("📋 조치 대상 인스턴스")
        
        selected_instances = []
        for instance in result['instances_without_keypair']:
            if st.checkbox(
                f"{instance['instance_id']} ({instance['instance_type']})",
                key=f"chk_select_instance_{instance['instance_id']}_{item_key}"
            ):
                selected_instances.append(instance)
        
        # 조치 실행 버튼 (실제로는 안내만 제공)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 수동 조치 체크리스트 생성", key=f"btn_generate_checklist_{item_key}"):
                if selected_instances:
                    st.subheader("📋 조치 체크리스트")
                    for instance in selected_instances:
                        st.markdown(f"""
                        **인스턴스: {instance['instance_id']}**
                        - [ ] Key Pair 생성 또는 준비
                        - [ ] 인스턴스 접속 확인
                        - [ ] ~/.ssh/authorized_keys 파일 백업
                        - [ ] 새 public key 추가
                        - [ ] 연결 테스트 완료
                        - [ ] 기존 접속 방법 제거 (보안상 권장)
                        """)
                else:
                    st.warning("조치할 인스턴스를 선택해주세요.")
        
        with col2:
            if st.button("✅ 수동 조치 완료 확인", key=f"btn_mark_complete_{item_key}"):
                # 조치 완료로 표시
                st.session_state[f'show_fix_{item_key}'] = False
                st.session_state[f'fix_completed_{item_key}'] = True
                st.success("✅ 수동 조치가 완료로 표시되었습니다. 재진단을 통해 확인해보세요.")
                st.rerun()
        
        # 돌아가기 버튼
        if st.button("↩️ 돌아가기", key=f"btn_back_from_fix_{item_key}"):
            st.session_state[f'show_fix_{item_key}'] = False
            st.rerun()