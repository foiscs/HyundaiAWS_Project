"""
WALB 진단 페이지 HTML 템플릿 모듈
CSS와 완전 분리된 순수 HTML 템플릿만 관리

Functions:
- get_hero_header_html(): 히어로 헤더 HTML 템플릿 (CSS 분리됨)
- get_diagnosis_loading_template(): 진단 로딩 템플릿 (CSS 클래스 사용)
- get_account_card_template(): 계정 정보 카드 템플릿 (CSS 클래스 기반)
- get_risk_badge_template(): 위험도 배지 템플릿 (CSS 클래스 기반)
- get_scroll_script(): 자동 스크롤 스크립트 템플릿
- get_diagnosis_completion_scroll(): 진단 완료 후 스크롤 스크립트
"""

def get_hero_header_html():
    """히어로 헤더 HTML 템플릿 반환 (CSS 분리됨)"""
    return """
    <div class="hero-header">
        <div class="floating-elements">
            <div class="floating-circle circle-1"></div>
            <div class="floating-circle circle-2"></div>
            <div class="floating-circle circle-3"></div>
        </div>
        <div class="hero-content">
            <div class="hero-icon">🔍</div>
            <div class="hero-text">
                <h1 class="hero-title">AWS 클라우드 보안 IaC 자동 점검</h1>
                <p class="hero-subtitle">KISA ISMS-P 매핑 31개 + SK Shieldus 2024 가이드라인 10개 항목</p>
            </div>
        </div>
    </div>
    """

def get_diagnosis_loading_template(item_name):
    """진단 로딩 템플릿 - CSS 클래스 기반으로 스타일 적용"""
    return f"""
    <div class="diagnosis-progress">
        <div class="progress-icon">🔍</div>
        <div class="progress-title">진단 진행 중...</div>
        <div class="progress-subtitle">{item_name} 분석 중</div>
    </div>
    """

def get_account_card_template(card_type, label, value, is_primary=False):
    """계정 정보 카드 템플릿 - 주요 카드와 일반 카드 구분하여 렌더링"""
    if is_primary:
        return f"""
        <div class="account-primary-card">
            <div class="account-primary-label">{label}</div>
            <div class="account-primary-value">{value}</div>
        </div>
        """
    else:
        return f"""
        <div class="account-info-card">
            <div class="account-info-label">{label}</div>
            <div class="account-info-value">{value}</div>
        </div>
        """

def get_risk_badge_template(icon, color, text):
    """위험도 배지 템플릿 - 위험도에 따른 색상 클래스 자동 적용"""
    risk_class = "risk-high" if "e53e3e" in color else "risk-medium" if "dd6b20" in color else "risk-low"
    return f"""
    <div class="risk-badge {risk_class}">
        <span style="margin-right: 4px; font-size: 1rem;">{icon}</span>
        <span style="font-weight: 600;">{text}</span>
    </div>
    """

def get_scroll_script(container_id):
    """자동 스크롤 스크립트 템플릿 - 특정 컨테이너로 부드럽게 스크롤"""
    return f"""
    <div id="{container_id}" style="position: absolute; height: 0; width: 0; visibility: hidden;"></div>
    <script>
    setTimeout(function() {{
        var element = document.getElementById('{container_id}');
        if (element) {{
            element.scrollIntoView({{
                behavior: 'smooth',
                block: 'center',
                inline: 'nearest'
            }});
        }}
    }}, 500);
    </script>
    """

def get_diagnosis_completion_scroll():
    """진단 완료 후 스크롤 스크립트 - 고정 위치로 부드럽게 스크롤"""
    return """
    <script>
    setTimeout(function() {
        window.scrollTo({top: 300, behavior: 'smooth'});
    }, 500);
    </script>
    """