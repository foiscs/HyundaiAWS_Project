"""
2.3 기타 서비스 정책 관리 진단
"""
import boto3
from ..base_checker import BaseChecker
import streamlit as st
from botocore.exceptions import ClientError

class OtherServicePolicyChecker(BaseChecker):
    """2.3 기타 서비스 정책 관리 진단"""
    
    @property
    def item_code(self):
        return "2.3"
    
    @property 
    def item_name(self):
        return "기타 서비스 정책 관리"
    
    def __init__(self, session=None):
        super().__init__(session)
        # 점검 대상 기타 서비스 과도한 권한 정책들
        self.overly_permissive_policies = {
            "arn:aws:iam::aws:policy/AWSOrganizationsFullAccess": "Organizations",
            "arn:aws:iam::aws:policy/CloudWatchFullAccess": "CloudWatch",
            "arn:aws:iam::aws:policy/AutoScalingFullAccess": "Auto Scaling",
            "arn:aws:iam::aws:policy/AWSCloudFormationFullAccess": "CloudFormation",
            "arn:aws:iam::aws:policy/AWSCloudTrail_FullAccess": "CloudTrail",
            "arn:aws:iam::aws:policy/AWSConfigUserAccess": "Config",
            "arn:aws:iam::aws:policy/AmazonSSMFullAccess": "Systems Manager",
            "arn:aws:iam::aws:policy/AmazonGuardDutyFullAccess": "GuardDuty",
            "arn:aws:iam::aws:policy/AmazonInspectorFullAccess": "Inspector",
            "arn:aws:iam::aws:policy/AWSSSOFullAccess": "Single Sign-On",
            "arn:aws:iam::aws:policy/AWSCertificateManagerFullAccess": "Certificate Manager",
            "arn:aws:iam::aws:policy/AWSKeyManagementServicePowerUser": "KMS",
            "arn:aws:iam::aws:policy/AWSWAF_FullAccess": "WAF",
            "arn:aws:iam::aws:policy/AWSShieldAdvancedFullAccess": "Shield",
            "arn:aws:iam::aws:policy/AWSSecurityHubFullAccess": "Security Hub",
            "arn:aws:iam::aws:policy/AWSDataPipeline_FullAccess": "Data Pipeline",
            "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess": "Glue",
            "arn:aws:iam::aws:policy/AmazonMSKFullAccess": "MSK",
            "arn:aws:iam::aws:policy/AWSBackupFullAccess": "Backup"
        }
    
    def run_diagnosis(self):
        """
        진단 수행
        - 주요 기타 서비스에 대해 과도한 권한(FullAccess/PowerUser)이 부여되었는지 점검
        """
        try:
            if self.session:
                iam = self.session.client('iam')
            else:
                iam = boto3.client('iam')
            
            findings = []
            
            for policy_arn, service_name in self.overly_permissive_policies.items():
                try:
                    paginator = iam.get_paginator('list_entities_for_policy')
                    for page in paginator.paginate(PolicyArn=policy_arn):
                        # 사용자에게 연결된 정책 확인
                        for user in page.get('PolicyUsers', []):
                            findings.append({
                                'type': 'user',
                                'name': user['UserName'],
                                'policy': policy_arn.split('/')[-1],
                                'service': service_name,
                                'policy_arn': policy_arn
                            })
                        
                        # 그룹에 연결된 정책 확인
                        for group in page.get('PolicyGroups', []):
                            findings.append({
                                'type': 'group',
                                'name': group['GroupName'],
                                'policy': policy_arn.split('/')[-1],
                                'service': service_name,
                                'policy_arn': policy_arn
                            })
                        
                        # 역할에 연결된 정책 확인
                        for role in page.get('PolicyRoles', []):
                            findings.append({
                                'type': 'role',
                                'name': role['RoleName'],
                                'policy': policy_arn.split('/')[-1],
                                'service': service_name,
                                'policy_arn': policy_arn
                            })
                            
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchEntity':
                        continue
                    else:
                        raise e

            # 위험도 계산
            finding_count = len(findings)
            risk_level = self.calculate_risk_level(
                finding_count,
                3 if finding_count > 5 else 2 if finding_count > 0 else 1
            )

            return {
                "status": "success",
                "findings": findings,
                "finding_count": finding_count,
                "services_affected": list(set([f['service'] for f in findings])),
                "risk_level": risk_level,
                "has_issues": finding_count > 0
            }

        except ClientError as e:
            return {
                "status": "error",
                "error_message": f"IAM 정책 정보를 가져오는 중 오류 발생: {str(e)}"
            }
    
    def render_result_ui(self, result, item_key, ui_handler):
        """2.3 진단 결과 UI 렌더링"""
        col1, col2 = st.columns(2)
        with col1:
            st.metric("과도한 권한 발견", result.get('finding_count', 0))
        with col2:
            affected_services = result.get('services_affected', [])
            st.metric("영향받는 서비스", len(affected_services))
        
        if affected_services:
            st.write(f"**영향받는 서비스:** {', '.join(affected_services)}")
        
        # 발견된 문제 표시
        if result.get('findings'):
            with st.expander("🔍 과도한 권한이 부여된 주체 목록"):
                for finding in result['findings']:
                    icon = {"user": "👤", "group": "👥", "role": "🛡️"}.get(finding['type'], "❓")
                    st.write(f"{icon} **{finding['type'].capitalize()}** `{finding['name']}` → **{finding['service']}** ({finding['policy']})")
        
        # 수동 조치 안내
        if result.get('has_issues', False):
            st.warning("⚠️ **중요**: 권한 변경은 운영에 큰 영향을 줄 수 있어 자동 조치가 제한됩니다.")
            st.error("  특히 'IAMFullAccess'와 같은 정책은 매우 위험하므로 신중한 검토가 필요합니다.")
            
            with st.expander("📋 수동 조치 가이드"):
                st.markdown("""
                **권장 조치 순서:**
                1. **IAM Access Analyzer 사용** - 실제 사용된 권한을 기반으로 세분화된 정책 생성
                2. **새 정책 생성 및 연결** - 최소 권한 원칙에 따른 맞춤형 정책 생성
                3. **충분한 테스트** - 새 정책이 업무에 지장이 없는지 확인
                4. **기존 정책 분리** - 아래 명령어 참고하여 과도한 정책 제거
                """)
                
                # CLI 명령어 예시 표시
                if result.get('findings'):
                    st.markdown("**CLI 명령어 예시:**")
                    cli_commands = []
                    for finding in result['findings'][:5]:  # 처음 5개만 표시
                        if finding['type'] == 'user':
                            cli_commands.append(f"aws iam detach-user-policy --user-name {finding['name']} --policy-arn {finding['policy_arn']}")
                        elif finding['type'] == 'group':
                            cli_commands.append(f"aws iam detach-group-policy --group-name {finding['name']} --policy-arn {finding['policy_arn']}")
                        elif finding['type'] == 'role':
                            cli_commands.append(f"aws iam detach-role-policy --role-name {finding['name']} --policy-arn {finding['policy_arn']}")
                    
                    for cmd in cli_commands:
                        st.code(cmd, language="bash")
                    
                    if len(result['findings']) > 5:
                        st.info(f"... 및 {len(result['findings']) - 5}개 추가 명령어")
        else:
            st.success("✅ 기타 주요 서비스에 과도한 권한이 부여된 주체가 없습니다.")
        
        # 재진단 버튼
        ui_handler.show_rediagnose_button(item_key)
    
    def render_fix_form(self, result, item_key, ui_handler):
        """2.3 조치 폼 UI 렌더링 - 수동 조치 안내만 제공"""
        st.markdown("**🔧 기타 서비스 정책 조치 안내**")
        st.error("⚠️ **자동 조치 제한**: 권한 변경은 운영에 큰 영향을 줄 수 있어 자동 조치를 제공하지 않습니다.")
            
        st.markdown("""
        **안전한 수동 조치 가이드:**
        1. **현재 사용 권한 분석** - IAM Access Analyzer로 실제 사용되는 권한 확인
        2. **최소 권한 정책 설계** - 업무에 필요한 최소한의 권한만 포함하는 정책 작성
        3. **단계적 적용** - 테스트 환경에서 먼저 검증 후 운영 환경 적용
        4. **모니터링** - 변경 후 응용 프로그램 정상 동작 여부 지속 확인
        """)
        
        # AWS 콘솔 링크 제공
        st.markdown("**유용한 AWS 콘솔 링크:**")
        st.markdown("- [IAM Access Analyzer](https://console.aws.amazon.com/access-analyzer/)")
        st.markdown("- [IAM 정책 시뮬레이터](https://policysim.aws.amazon.com/)")
        st.markdown("- [IAM 사용자](https://console.aws.amazon.com/iam/home#/users)")
        st.markdown("- [IAM 그룹](https://console.aws.amazon.com/iam/home#/groups)")
        st.markdown("- [IAM 역할](https://console.aws.amazon.com/iam/home#/roles)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Access Analyzer 사용법", key=f"guide_{item_key}", type="primary"):
                st.info("""
                **IAM Access Analyzer 사용법:**
                1. IAM 콘솔 → Access Analyzer 선택
                2. 분석기 생성 (조직 또는 계정 단위)
                3. 정책 생성 → 기존 역할/사용자의 CloudTrail 로그 분석
                4. 생성된 정책을 검토하고 필요에 따라 수정
                5. 새 정책을 적용하고 기존 과도한 정책 제거
                """)
        
        with col2:
            if st.button("❌ 닫기", key=f"close_{item_key}"):
                st.session_state[f'show_fix_{item_key}'] = False
                st.rerun()
            
    def execute_fix(self, selected_items):
        """조치 실행 (BaseChecker 추상 메서드 구현) - 자동 조치 제한"""
        return [{
            "user": "보안 정책",
            "action": "자동 조치 제한",
            "status": "no_action",
            "message": "권한 변경은 운영에 큰 영향을 줄 수 있어 수동 조치만 가능합니다. 위의 가이드를 참고하여 안전하게 조치하세요."
        }]