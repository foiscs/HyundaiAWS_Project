// WALB Flask Main JavaScript

// 유틸리티 함수들
const WALB = {
    // API 호출 헬퍼
    api: {
        async get(url) {
            try {
                const response = await fetch(url);
                return await response.json();
            } catch (error) {
                console.error('API GET Error:', error);
                throw error;
            }
        },
        
        async post(url, data) {
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                return await response.json();
            } catch (error) {
                console.error('API POST Error:', error);
                throw error;
            }
        }
    },
    
    // 로딩 상태 관리
    loading: {
        show(element) {
            if (element) {
                element.disabled = true;
                element.innerHTML = '<span class="loading-spinner"></span> 처리중...';
            }
        },
        
        hide(element, originalText) {
            if (element) {
                element.disabled = false;
                element.innerHTML = originalText;
            }
        }
    },
    
    // 알림 메시지
    toast: {
        show(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;
            
            const bgColor = {
                'success': 'bg-green-500',
                'error': 'bg-red-500',
                'warning': 'bg-yellow-500',
                'info': 'bg-blue-500'
            }[type] || 'bg-blue-500';
            
            toast.classList.add(bgColor);
            toast.innerHTML = `
                <div class="flex items-center text-white">
                    <span class="mr-2">${this.getIcon(type)}</span>
                    <span>${message}</span>
                    <button onclick="this.parentElement.parentElement.remove()" 
                            class="ml-2 text-white hover:text-gray-200">
                        ✕
                    </button>
                </div>
            `;
            
            document.body.appendChild(toast);
            
            // 애니메이션
            setTimeout(() => toast.classList.remove('translate-x-full'), 100);
            setTimeout(() => {
                toast.classList.add('translate-x-full');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        },
        
        getIcon(type) {
            const icons = {
                'success': '✅',
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️'
            };
            return icons[type] || 'ℹ️';
        }
    },
    
    // 모달 관리
    modal: {
        show(content, title = '') {
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50';
            modal.innerHTML = `
                <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4 transform transition-all duration-300 scale-95">
                    ${title ? `<h3 class="text-lg font-semibold mb-4">${title}</h3>` : ''}
                    <div class="mb-4">${content}</div>
                    <div class="flex justify-end space-x-2">
                        <button onclick="WALB.modal.close()" 
                                class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors">
                            닫기
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            setTimeout(() => modal.querySelector('.bg-white').classList.remove('scale-95'), 100);
            
            // ESC 키로 닫기
            const closeHandler = (e) => {
                if (e.key === 'Escape') {
                    this.close();
                    document.removeEventListener('keydown', closeHandler);
                }
            };
            document.addEventListener('keydown', closeHandler);
            
            return modal;
        },
        
        close() {
            const modal = document.querySelector('.fixed.inset-0.z-50');
            if (modal) {
                modal.querySelector('.bg-white').classList.add('scale-95');
                setTimeout(() => modal.remove(), 300);
            }
        }
    },
    
    // 폼 검증
    validate: {
        required(value, fieldName) {
            if (!value || value.trim() === '') {
                throw new Error(`${fieldName}은(는) 필수 입력 항목입니다.`);
            }
        },
        
        email(value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (value && !emailRegex.test(value)) {
                throw new Error('올바른 이메일 형식을 입력해주세요.');
            }
        },
        
        awsAccountId(value) {
            if (value && (!/^\d{12}$/.test(value))) {
                throw new Error('AWS 계정 ID는 12자리 숫자여야 합니다.');
            }
        }
    }
};

// 전역 이벤트 리스너
document.addEventListener('DOMContentLoaded', function() {
    // 실시간 시간 업데이트
    function updateTime() {
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = now.toLocaleString('ko-KR');
        }
    }
    
    updateTime();
    setInterval(updateTime, 1000);
    
    // 네비게이션 활성 상태 업데이트
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('aside nav a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('bg-blue-50', 'text-blue-700');
        }
    });
    
    // 모바일 사이드바 토글 (추후 구현)
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('aside');
            sidebar.classList.toggle('open');
        });
    }
});

// AWS 관련 유틸리티
const AWS_UTILS = {
    // 리전 목록
    regions: [
        { code: 'us-east-1', name: 'US East (N. Virginia)' },
        { code: 'us-west-2', name: 'US West (Oregon)' },
        { code: 'ap-northeast-2', name: 'Asia Pacific (Seoul)' },
        { code: 'ap-northeast-1', name: 'Asia Pacific (Tokyo)' },
        { code: 'eu-west-1', name: 'Europe (Ireland)' }
    ],
    
    // 계정 ID 마스킹
    maskAccountId(accountId) {
        if (!accountId || accountId.length !== 12) return accountId;
        return accountId.substring(0, 4) + '****' + accountId.substring(8);
    },
    
    // Role ARN 검증
    validateRoleArn(arn) {
        const arnPattern = /^arn:aws:iam::\d{12}:role\/[\w+=,.@-]+$/;
        return arnPattern.test(arn);
    }
};

// 진단 관련 유틸리티
const DIAGNOSIS_UTILS = {
    // 위험도별 색상
    riskColors: {
        'high': 'text-red-600 bg-red-50 border-red-200',
        'medium': 'text-yellow-600 bg-yellow-50 border-yellow-200',
        'low': 'text-green-600 bg-green-50 border-green-200'
    },
    
    // 위험도별 아이콘
    riskIcons: {
        'high': '🔴',
        'medium': '🟡', 
        'low': '🟢'
    },
    
    // 진단 결과 포맷팅
    formatResult(result) {
        return {
            icon: this.riskIcons[result.risk_level] || '⚪',
            color: this.riskColors[result.risk_level] || 'text-gray-600 bg-gray-50 border-gray-200',
            message: result.message || '진단 완료'
        };
    }
};

// 전역으로 노출
window.WALB = WALB;
window.AWS_UTILS = AWS_UTILS;
window.DIAGNOSIS_UTILS = DIAGNOSIS_UTILS;