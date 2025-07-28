/**
 * diagnosis.js - SK Shieldus 보안 진단 페이지 JavaScript
 * mainHub의 진단 기능을 Flask용으로 이식
 */

class DiagnosisManager {
    constructor() {
        this.selectedAccountId = null;
        this.diagnosisInProgress = false;
        this.diagnosisResults = new Map();
        
        this.initializeEventListeners();
        this.initializeUI();
    }
    
    initializeEventListeners() {
        // 계정 카드 클릭 이벤트는 이미 HTML에서 onclick으로 처리됨
        
        // 진단 버튼들 이벤트 리스너
        document.addEventListener('click', (e) => {
            // 개별 진단 버튼
            if (e.target.matches('.btn.btn-primary[onclick*="runSingleDiagnosis"]')) {
                e.preventDefault();
                const itemCode = this.extractItemCodeFromOnclick(e.target.getAttribute('onclick'));
                if (itemCode) {
                    this.runSingleDiagnosis(itemCode);
                }
            }
            
            // 전체 진단 버튼
            if (e.target.matches('button[onclick*="runAllDiagnosis"]')) {
                e.preventDefault();
                this.runAllDiagnosis();
            }
            
            // 연결 테스트 버튼
            if (e.target.matches('button[onclick*="testConnection"]')) {
                e.preventDefault();
                this.testConnection();
            }
            
            // 카테고리 진단 버튼
            if (e.target.matches('button[onclick*="runCategoryDiagnosis"]')) {
                e.preventDefault();
                const category = this.extractCategoryFromOnclick(e.target.getAttribute('onclick'));
                if (category) {
                    this.runCategoryDiagnosis(category);
                }
            }
            
            // 재진단 버튼
            if (e.target.matches('button[onclick*="rediagnose"]')) {
                e.preventDefault();
                const itemElement = e.target.closest('.diagnosis-item');
                if (itemElement) {
                    const itemCode = itemElement.dataset.itemCode;
                    this.runSingleDiagnosis(itemCode);
                }
            }
        });
    }
    
    initializeUI() {
        // 페이지 로드 시 선택된 계정이 있으면 자동 선택
        const selectedAccountElement = document.querySelector('.account-card.selected');
        if (selectedAccountElement) {
            const accountId = selectedAccountElement.dataset.accountId;
            this.selectAccount(accountId);
        }
    }
    
    // HTML onclick에서 항목 코드 추출
    extractItemCodeFromOnclick(onclickValue) {
        const match = onclickValue.match(/runSingleDiagnosis\(['"]([^'"]+)['"]\)/);
        return match ? match[1] : null;
    }
    
    // HTML onclick에서 카테고리 추출
    extractCategoryFromOnclick(onclickValue) {
        const match = onclickValue.match(/runCategoryDiagnosis\(['"]([^'"]+)['"]\)/);
        return match ? match[1] : null;
    }
    
    // 계정 선택 (전역 함수에서 호출됨)
    selectAccount(accountId) {
        this.selectedAccountId = accountId;
        
        // 기존 선택 해제
        document.querySelectorAll('.account-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // 새 선택 적용
        const selectedCard = document.querySelector(`[data-account-id="${accountId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        // 제어판과 진단 항목 표시
        const controlPanel = document.getElementById('controlPanel');
        const diagnosisItems = document.getElementById('diagnosisItems');
        
        if (controlPanel) {
            controlPanel.style.display = 'block';
        }
        if (diagnosisItems) {
            diagnosisItems.style.display = 'block';
        }
        
        // 부드러운 스크롤
        setTimeout(() => {
            if (controlPanel) {
                controlPanel.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }, 300);
    }
    
    // 연결 테스트
    async testConnection() {
        if (!this.selectedAccountId) {
            this.showToast('계정을 선택해주세요.', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/diagnosis/api/test-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account_id: this.selectedAccountId
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.showToast(
                    `✅ 연결 테스트 성공!\n계정 ID: ${result.account_id}\n접근 가능 리전: ${result.regions}개`,
                    'success'
                );
            } else {
                this.showToast(`❌ 연결 테스트 실패\n${result.error_message}`, 'error');
            }
        } catch (error) {
            console.error('Connection test error:', error);
            this.showToast(`연결 테스트 중 오류가 발생했습니다: ${error.message}`, 'error');
        }
    }
    
    // 개별 진단 실행
    async runSingleDiagnosis(itemCode) {
        if (!this.selectedAccountId) {
            this.showToast('계정을 선택해주세요.', 'warning');
            return;
        }
        
        const statusElement = document.getElementById(`status-${itemCode}`);
        const resultElement = document.getElementById(`result-${itemCode}`);
        
        if (!statusElement || !resultElement) {
            console.error(`Status or result element not found for item: ${itemCode}`);
            return;
        }
        
        // 진행 상태로 변경
        statusElement.innerHTML = '<span class="status-badge status-running">진행중</span>';
        resultElement.style.display = 'none';
        
        try {
            const response = await fetch('/diagnosis/api/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account_id: this.selectedAccountId,
                    item_code: itemCode
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                statusElement.innerHTML = '<span class="status-badge status-completed">완료</span>';
                this.displayDiagnosisResult(itemCode, result);
                this.diagnosisResults.set(itemCode, result);
            } else {
                statusElement.innerHTML = '<span class="status-badge status-failed">실패</span>';
                this.displayDiagnosisError(itemCode, result.message);
            }
        } catch (error) {
            console.error(`Diagnosis error for ${itemCode}:`, error);
            statusElement.innerHTML = '<span class="status-badge status-failed">실패</span>';
            this.displayDiagnosisError(itemCode, `진단 중 오류가 발생했습니다: ${error.message}`);
        }
    }
    
    // 전체 진단 실행
    async runAllDiagnosis() {
        if (!this.selectedAccountId) {
            this.showToast('계정을 선택해주세요.', 'warning');
            return;
        }
        
        if (this.diagnosisInProgress) {
            this.showToast('이미 진단이 진행 중입니다.', 'warning');
            return;
        }
        
        this.diagnosisInProgress = true;
        this.showProgressModal();
        
        try {
            const response = await fetch('/diagnosis/api/run-all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account_id: this.selectedAccountId
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                this.updateProgressModal(100, result.success_count, result.failed_count);
                
                // 개별 결과 업데이트
                Object.entries(result.results).forEach(([itemCode, itemResult]) => {
                    const statusElement = document.getElementById(`status-${itemCode}`);
                    if (statusElement) {
                        if (itemResult.status === 'success') {
                            statusElement.innerHTML = '<span class="status-badge status-completed">완료</span>';
                            this.displayDiagnosisResult(itemCode, itemResult);
                        } else {
                            statusElement.innerHTML = '<span class="status-badge status-failed">실패</span>';
                            this.displayDiagnosisError(itemCode, itemResult.message);
                        }
                    }
                });
                
                setTimeout(() => {
                    this.closeProgressModal();
                    this.showToast(
                        `✅ 전체 진단 완료!\n성공: ${result.success_count}개\n실패: ${result.failed_count}개`,
                        'success'
                    );
                }, 1000);
            } else {
                this.showToast(`❌ 전체 진단 실패\n${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Batch diagnosis error:', error);
            this.showToast(`전체 진단 중 오류가 발생했습니다: ${error.message}`, 'error');
        } finally {
            this.diagnosisInProgress = false;
            this.closeProgressModal();
        }
    }
    
    // 카테고리별 진단 실행
    async runCategoryDiagnosis(category) {
        if (!this.selectedAccountId) {
            this.showToast('계정을 선택해주세요.', 'warning');
            return;
        }
        
        // 해당 카테고리의 모든 항목 코드 수집
        const categoryItems = document.querySelectorAll(`[data-category="${category}"] .diagnosis-item`);
        const itemCodes = Array.from(categoryItems).map(item => item.dataset.itemCode);
        
        if (itemCodes.length === 0) {
            this.showToast('진단할 항목이 없습니다.', 'warning');
            return;
        }
        
        // 각 항목을 순차적으로 진단
        for (const itemCode of itemCodes) {
            await this.runSingleDiagnosis(itemCode);
            // 잠시 대기
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        this.showToast(`${category} 카테고리 진단이 완료되었습니다.`, 'success');
    }
    
    // 진단 결과 표시
    displayDiagnosisResult(itemCode, result) {
        const resultElement = document.getElementById(`result-${itemCode}`);
        if (!resultElement) return;
        
        const diagnosisResult = result.result;
        let resultHTML = '<div class="result-summary">';
        
        if (diagnosisResult && diagnosisResult.status === 'success') {
            // 성공 결과 표시
            resultHTML += `
                <div class="result-header">
                    <div class="result-status success">✅ 진단 완료</div>
                    <div class="result-time">${new Date(result.executed_at).toLocaleString()}</div>
                </div>
                <div class="result-content">
                    <div class="result-item">
                        <strong>위험도:</strong> 
                        <span class="risk-level risk-${diagnosisResult.risk_level || 'low'}">
                            ${diagnosisResult.risk_level || 'low'}
                        </span>
                    </div>
                    <div class="result-item">
                        <strong>요약:</strong> ${diagnosisResult.summary || '진단 완료'}
                    </div>
            `;
            
            // 상세 정보 표시
            if (diagnosisResult.details) {
                resultHTML += '<div class="result-details">';
                Object.entries(diagnosisResult.details).forEach(([key, value]) => {
                    if (typeof value === 'object' && value !== null) {
                        resultHTML += `<div class="detail-section">
                            <strong>${key}:</strong>
                            <div class="detail-content">`;
                        
                        if (value.count !== undefined) {
                            resultHTML += `<div>개수: ${value.count}</div>`;
                        }
                        if (value.users && Array.isArray(value.users)) {
                            resultHTML += `<div>목록: ${value.users.join(', ') || '없음'}</div>`;
                        }
                        if (value.recommendation) {
                            resultHTML += `<div class="recommendation">권장사항: ${value.recommendation}</div>`;
                        }
                        
                        resultHTML += '</div></div>';
                    } else {
                        resultHTML += `<div class="result-item"><strong>${key}:</strong> ${value}</div>`;
                    }
                });
                resultHTML += '</div>';
            }
            
            // 자동 조치 버튼 표시
            if (diagnosisResult.fix_options && diagnosisResult.fix_options.length > 0) {
                resultHTML += '<div class="fix-actions">';
                diagnosisResult.fix_options.forEach((option, index) => {
                    resultHTML += `
                        <button class="btn btn-sm btn-outline fix-btn" 
                                data-item-code="${itemCode}" 
                                data-fix-type="${option.type}"
                                onclick="showFixOptions('${itemCode}', ${index})">
                            🔧 ${option.title}
                        </button>
                    `;
                });
                resultHTML += '</div>';
            }
            
            resultHTML += '</div>';
        } else {
            // 오류 결과 표시
            resultHTML += `
                <div class="result-header">
                    <div class="result-status error">❌ 진단 실패</div>
                    <div class="result-time">${new Date().toLocaleString()}</div>
                </div>
                <div class="result-content">
                    <div class="error-message">${diagnosisResult?.error_message || result.message || '알 수 없는 오류'}</div>
                </div>
            `;
        }
        
        resultHTML += '</div>';
        
        resultElement.innerHTML = resultHTML;
        resultElement.style.display = 'block';
    }
    
    // 진단 오류 표시
    displayDiagnosisError(itemCode, errorMessage) {
        const resultElement = document.getElementById(`result-${itemCode}`);
        if (!resultElement) return;
        
        const resultHTML = `
            <div class="result-summary">
                <div class="result-header">
                    <div class="result-status error">❌ 진단 실패</div>
                    <div class="result-time">${new Date().toLocaleString()}</div>
                </div>
                <div class="result-content">
                    <div class="error-message">${errorMessage}</div>
                </div>
            </div>
        `;
        
        resultElement.innerHTML = resultHTML;
        resultElement.style.display = 'block';
    }
    
    // 진행 상황 모달 표시
    showProgressModal() {
        const modal = document.getElementById('progressModal');
        if (modal) {
            modal.style.display = 'flex';
            this.updateProgressModal(0, 0, 0);
        }
    }
    
    // 진행 상황 모달 닫기
    closeProgressModal() {
        const modal = document.getElementById('progressModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    // 진행 상황 업데이트
    updateProgressModal(percentage, completed, failed) {
        const percentageElement = document.getElementById('progressPercentage');
        const completedElement = document.getElementById('completedCount');
        const failedElement = document.getElementById('failedCount');
        const progressFill = document.getElementById('progressFill');
        
        if (percentageElement) percentageElement.textContent = `${percentage}%`;
        if (completedElement) completedElement.textContent = completed;
        if (failedElement) failedElement.textContent = failed;
        if (progressFill) progressFill.style.width = `${percentage}%`;
    }
    
    // 토스트 메시지 표시
    showToast(message, type = 'info') {
        // 간단한 토스트 구현
        console.log(`[${type.toUpperCase()}] ${message}`);
        alert(message); // 임시로 alert 사용, 추후 더 나은 UI로 교체 가능
    }
}

// 전역 변수로 DiagnosisManager 인스턴스 생성
let diagnosisManager;

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    diagnosisManager = new DiagnosisManager();
});

// 전역 함수들 (HTML에서 onclick으로 호출됨)
function selectAccount(accountId) {
    if (diagnosisManager) {
        diagnosisManager.selectAccount(accountId);
    }
}

function testConnection() {
    if (diagnosisManager) {
        diagnosisManager.testConnection();
    }
}

function runSingleDiagnosis(itemCode) {
    if (diagnosisManager) {
        diagnosisManager.runSingleDiagnosis(itemCode);
    }
}

function runAllDiagnosis() {
    if (diagnosisManager) {
        diagnosisManager.runAllDiagnosis();
    }
}

function runCategoryDiagnosis(category) {
    if (diagnosisManager) {
        diagnosisManager.runCategoryDiagnosis(category);
    }
}

function closeProgressModal() {
    if (diagnosisManager) {
        diagnosisManager.closeProgressModal();
    }
}

function rediagnose(button) {
    if (diagnosisManager) {
        const itemElement = button.closest('.diagnosis-item');
        if (itemElement) {
            const itemCode = itemElement.dataset.itemCode;
            diagnosisManager.runSingleDiagnosis(itemCode);
        }
    }
}