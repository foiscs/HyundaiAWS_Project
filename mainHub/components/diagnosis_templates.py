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
    """히어로 헤더 HTML 템플릿 반환 (CSS 포함)"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif;
        }
        .hero-header {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            color: white;
            padding: 2.5rem 2rem;
            border-radius: 16px;
            margin: 1rem 0 2rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        .hero-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }
        .hero-content {
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }
        .hero-icon {
            font-size: 3.5rem;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
            animation: float 3s ease-in-out infinite;
        }
        .hero-text {
            flex: 1;
        }
        .hero-title {
            font-size: 2.25rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            background: linear-gradient(45deg, #ffffff, #cbd5e0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .hero-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin: 0;
            font-weight: 400;
        }
        .floating-elements {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            overflow: hidden;
        }
        .floating-circle {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            animation: float-circle 6s ease-in-out infinite;
        }
        .circle-1 {
            width: 60px;
            height: 60px;
            top: 20%;
            right: 10%;
            animation-delay: 0s;
        }
        .circle-2 {
            width: 40px;
            height: 40px;
            top: 60%;
            right: 20%;
            animation-delay: 2s;
        }
        .circle-3 {
            width: 80px;
            height: 80px;
            top: 10%;
            left: 15%;
            animation-delay: 4s;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        @keyframes float-circle {
            0%, 100% { transform: translateY(0px) scale(1); opacity: 0.3; }
            50% { transform: translateY(-20px) scale(1.1); opacity: 0.6; }
        }
        </style>
    </head>
    <body>
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
    </body>
    </html>
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

def get_expander_color_script():
    """Expander 헤더에 중요도별 색상을 적용하는 스크립트"""
    return """
    <script>
    function applyExpanderColors() {
        // Streamlit expander 헤더들을 찾아서 중요도별 색상 클래스 추가
        const expanderHeaders = document.querySelectorAll('.streamlit-expanderHeader');
        
        expanderHeaders.forEach(function(header) {
            const text = header.textContent || header.innerText;
            
            // 기존 중요도 클래스 제거
            header.classList.remove('importance-high', 'importance-medium', 'importance-low');
            
            if (text.includes('🔴 상')) {
                header.classList.add('importance-high');
            } else if (text.includes('🟡 중')) {
                header.classList.add('importance-medium');
            } else if (text.includes('🟢 하')) {
                header.classList.add('importance-low');
            }
        });
    }
    
    // 페이지 로드 후 실행
    setTimeout(applyExpanderColors, 1000);
    
    // DOM 변경 감지하여 재적용 (Streamlit의 동적 렌더링 대응)
    const observer = new MutationObserver(function(mutations) {
        let shouldReapply = false;
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && 
                        (node.classList && node.classList.contains('streamlit-expanderHeader') ||
                         node.querySelector && node.querySelector('.streamlit-expanderHeader'))) {
                        shouldReapply = true;
                    }
                });
            }
        });
        if (shouldReapply) {
            setTimeout(applyExpanderColors, 200);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    </script>
    """