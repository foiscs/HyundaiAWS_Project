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
        st.subheader("🔧 Key Pair 수동 조치 안내")
        
        if not result.get('instances_without_keypair'):
            st.info("조치할 인스턴스가 없습니다.")
            return
        
        st.warning("⚠️ **Key Pair는 실행 중인 인스턴스에 자동 할당할 수 없습니다. (자동 조치 불가능)**")
        
        st.markdown("""
        ### 📋 수동 조치 방법
        
        **방법 1: 기존 인스턴스에 Key 추가**
        ```bash
        # 1. 인스턴스에 접속 (EC2 Instance Connect 등 이용)
        # 2. authorized_keys에 새 public key 추가
        echo "ssh-rsa AAAAB3... your-key" >> ~/.ssh/authorized_keys
        chmod 600 ~/.ssh/authorized_keys
        ```
        
        **방법 2: AMI로 새 인스턴스 생성**
        1. EC2 콘솔에서 기존 인스턴스의 AMI 생성
        2. 새 인스턴스 시작 시 Key Pair 선택
        3. 기존 인스턴스 교체
        
        ---
        **조치 완료 후 재진단을 실행하여 결과를 확인하세요.**
        """)
        
        # 돌아가기 버튼
        if st.button("↩️ 돌아가기", key=f"btn_back_from_fix_{item_key}"):
            st.session_state[f'show_fix_{item_key}'] = False
            st.rerun()