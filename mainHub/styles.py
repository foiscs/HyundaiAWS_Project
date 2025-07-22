"""
AWS 계정 연결 웹 인터페이스용 커스텀 CSS 스타일
Tailwind CSS 스타일을 Streamlit용 CSS로 변환

- get_main_styles: 전체 페이지 배경, 폰트, 기본 레이아웃 스타일
- get_card_styles: 흰색 배경 카드, 선택 가능한 카드 스타일
- get_step_indicator_styles: 단계 표시기 원형, 연결선, 색상 스타일
- get_info_box_styles: 정보/경고/에러/성공 박스 타입별 색상 스타일
- get_code_block_styles: JSON 코드 블록 다크 테마, 복사 버튼 스타일
- get_test_result_styles: 연결 테스트 결과 테이블, 성공/실패 표시 스타일
- get_loading_styles: 로딩 스피너 회전 애니메이션, 진행 메시지 스타일
- get_all_styles: 모든 CSS 스타일을 통합하여 한 번에 주입
"""

def get_main_styles():
    """
    메인 페이지 전체 스타일 정의
    - 전체 배경, 폰트, 기본 레이아웃 스타일
    """
    return """
    <style>
    /* 전체 페이지 배경 */
    .stApp {
        background-color: #F9FAFB;
    }
    
    /* 메인 컨테이너 */
    .main-container {
        width: 100%;
        padding: 1.5rem;
    }
    
    /* 제목 스타일 */
    .main-title {
        color: #111827;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    </style>
    """

def get_card_styles():
    """
    카드 컴포넌트 스타일 정의
    - 흰색 배경, 그림자, 둥근 모서리
    """
    return """
    <style>
    /* 기본 카드 스타일 */
    .custom-card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #E5E7EB;
    }
    
    /* 선택 가능한 카드 */
    .selectable-card {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s;
        border: 2px solid #E5E7EB;
    }
    
    .selectable-card:hover {
        border-color: #D1D5DB;
    }
    
    /* 선택된 카드 - Cross Account Role (파란색) */
    .selected-role {
        border-color: #3B82F6;
        background-color: #EFF6FF;
    }
    
    /* 선택된 카드 - Access Key (주황색) */
    .selected-key {
        border-color: #F59E0B;
        background-color: #FFFBEB;
    }
    </style>
    """

def get_step_indicator_styles():
    """
    단계 표시기 스타일 정의
    - 원형 단계 표시, 연결선, 색상 변화
    """
    return """
    <style>
    /* 단계 표시기 컨테이너 */
    .step-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 2rem 0;
        padding: 0 1rem;
    }
    
    /* 개별 단계 */
    .step-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    /* 단계 원형 표시 */
    .step-circle {
        width: 2rem;
        height: 2rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.875rem;
    }
    
    /* 완료된 단계 */
    .step-completed {
        background-color: #10B981;
        color: white;
    }
    
    /* 현재 진행 단계 */
    .step-active {
        background-color: #3B82F6;
        color: white;
    }
    
    /* 대기 단계 */
    .step-pending {
        background-color: #E5E7EB;
        color: #6B7280;
    }
    
    /* 단계 제목 */
    .step-title {
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .step-title.completed {
        color: #10B981;
    }
    
    .step-title.active {
        color: #3B82F6;
    }
    
    .step-title.pending {
        color: #6B7280;
    }
    
    /* 연결선 */
    .step-connector {
        flex: 1;
        height: 1px;
        background-color: #E5E7EB;
        margin: 0 1rem;
    }
    </style>
    """

def get_info_box_styles():
    """
    정보 박스 스타일 정의
    - info, warning, error, success 타입별 색상
    """
    return """
    <style>
    /* 기본 정보 박스 */
    .info-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }
    
    /* 정보 타입 */
    .info-box.info {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #1E40AF;
    }
    
    /* 경고 타입 */
    .info-box.warning {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        color: #92400E;
    }
    
    /* 에러 타입 */
    .info-box.error {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        color: #B91C1C;
    }
    
    /* 성공 타입 */
    .info-box.success {
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        color: #065F46;
    }
    
    .info-box-content {
        flex: 1;
    }
    
    .info-box-title {
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .info-box-text {
        font-size: 0.875rem;
        line-height: 1.4;
    }
    </style>
    """

def get_code_block_styles():
    """
    JSON 코드 블록 스타일 정의
    - 다크 테마, 구문 강조, 복사 버튼
    """
    return """
    <style>
    /* 코드 블록 컨테이너 */
    .code-container {
        margin: 1rem 0;
    }
    
    .code-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .code-title {
        font-weight: 600;
        color: #111827;
    }
    
    .copy-button {
        background-color: #3B82F6;
        color: white;
        border: none;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .copy-button:hover {
        background-color: #2563EB;
    }
    
    /* JSON 코드 블록 */
    .json-code {
        background-color: #1F2937;
        color: #10B981;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.75rem;
        overflow-x: auto;
        max-height: 300px;
        overflow-y: auto;
    }
    </style>
    """

def get_test_result_styles():
    """
    연결 테스트 결과 스타일 정의
    - 테이블, 성공/실패 표시, 로딩 상태
    """
    return """
    <style>
    /* 테스트 결과 컨테이너 */
    .test-result-container {
        text-align: center;
        padding: 2rem;
    }
    
    .test-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .test-title {
        font-size: 1.125rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .test-description {
        color: #6B7280;
        margin-bottom: 1rem;
    }
    
    /* 성공 상태 */
    .test-success .test-title {
        color: #065F46;
    }
    
    .test-success .test-description {
        color: #047857;
    }
    
    /* 실패 상태 */
    .test-failed .test-title {
        color: #B91C1C;
    }
    
    .test-failed .test-description {
        color: #DC2626;
    }
    
    /* 권한 테이블 */
    .permission-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1rem;
    }
    
    .permission-table th,
    .permission-table td {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #E5E7EB;
    }
    
    .permission-table th {
        background-color: #F9FAFB;
        font-weight: 600;
        color: #374151;
    }
    
    .permission-status {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .permission-success {
        color: #10B981;
    }
    
    .permission-failed {
        color: #EF4444;
    }
    </style>
    """

def get_loading_styles():
    """
    로딩 스피너 및 애니메이션 스타일
    """
    return """
    <style>
    /* 로딩 컨테이너 */
    .loading-container {
        text-align: center;
        padding: 2rem;
    }
    
    .loading-spinner {
        font-size: 3rem;
        animation: spin 2s linear infinite;
        margin-bottom: 1rem;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .loading-message {
        color: #6B7280;
        margin-bottom: 0.5rem;
    }
    
    .loading-steps {
        font-size: 0.875rem;
        color: #9CA3AF;
    }
    
    .loading-steps div {
        margin: 0.25rem 0;
    }
    </style>
    """

def get_all_styles():
    """
    모든 스타일을 합쳐서 반환
    - 한 번에 모든 CSS를 주입하기 위한 함수
    """
    return (
        get_main_styles() +
        get_card_styles() +
        get_step_indicator_styles() +
        get_info_box_styles() +
        get_code_block_styles() +
        get_test_result_styles() +
        get_loading_styles()
    )