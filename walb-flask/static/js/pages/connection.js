// Connection Page JavaScript

class ConnectionManager {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.selectedMethod = null;
        this.formData = {};
        this.isEditMode = false;
        this.editAccount = null;

        this.initializeEventListeners();
        this.updateStepDisplay();
    }

    initializeEventListeners() {
        // Navigation buttons
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const saveBtn = document.getElementById('save-btn');

        if (prevBtn) prevBtn.addEventListener('click', () => this.previousStep());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextStep());
        if (saveBtn) saveBtn.addEventListener('click', () => this.saveAccount());

        // Connection method selection
        document.querySelectorAll('.connection-method-card').forEach((card) => {
            card.addEventListener('click', (e) => this.selectConnectionMethod(e));
        });

        // Test connection button
        const testBtn = document.getElementById('test-connection-btn');
        if (testBtn) testBtn.addEventListener('click', () => this.testConnection());

        // Form validation
        const form = document.getElementById('account-form');
        if (form) {
            form.addEventListener('input', (e) => this.handleFormInput(e));
            form.addEventListener('change', (e) => this.handleFormChange(e));
        }

        // Real-time field validation
        this.setupFieldValidation();
    }

    selectConnectionMethod(event) {
        const card = event.currentTarget;
        const method = card.dataset.method;

        // Update UI
        document.querySelectorAll('.connection-method-card').forEach((c) => {
            c.classList.remove('selected');
            c.querySelector('div').classList.remove('border-blue-500');
            c.querySelector('div').classList.add('border-gray-200');
        });

        card.classList.add('selected');
        card.querySelector('div').classList.add('border-blue-500');
        card.querySelector('div').classList.remove('border-gray-200');

        this.selectedMethod = method;
        this.updateNextButton();
    }

    updateStepDisplay() {
        // Update step indicators
        document.querySelectorAll('.step-item').forEach((item, index) => {
            const stepNum = index + 1;
            const circle = item.querySelector('.step-circle');

            // Remove all state classes
            item.classList.remove('active', 'completed');

            if (stepNum < this.currentStep) {
                item.classList.add('completed');
                // For completed steps, show checkmark instead of number
                if (circle) {
                    circle.textContent = '';
                }
            } else if (stepNum === this.currentStep) {
                item.classList.add('active');
                // For active step, show the step number
                if (circle) {
                    circle.textContent = stepNum;
                }
            } else {
                // For pending steps, show the step number
                if (circle) {
                    circle.textContent = stepNum;
                }
            }
        });

        // Update step lines
        document.querySelectorAll('.step-line').forEach((line, index) => {
            line.classList.remove('completed');
            if (index + 1 < this.currentStep) {
                line.classList.add('completed');
            }
        });

        // Show/hide step content
        document.querySelectorAll('.step-content').forEach((content, index) => {
            if (index + 1 === this.currentStep) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        });

        // Update navigation buttons
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const saveBtn = document.getElementById('save-btn');

        // 수정 모드에서는 3단계 이전 버튼 비활성화
        if (this.isEditMode) {
            prevBtn.disabled = this.currentStep <= 3;
        } else {
            prevBtn.disabled = this.currentStep === 1;
        }

        if (this.currentStep === this.totalSteps) {
            nextBtn.classList.add('hidden');
            saveBtn.classList.remove('hidden');
        } else {
            nextBtn.classList.remove('hidden');
            saveBtn.classList.add('hidden');
        }
    }

    // 특정 단계로 직접 이동하는 메서드 (수정 모드용)
    showStep(stepNumber) {
        if (stepNumber >= 1 && stepNumber <= this.totalSteps) {
            this.currentStep = stepNumber;
            this.updateStepDisplay();
        }
    }

    updateNextButton() {
        const nextBtn = document.getElementById('next-btn');

        if (this.currentStep === 1) {
            nextBtn.disabled = !this.selectedMethod;
        } else if (this.currentStep === 2) {
            nextBtn.disabled = false; // Permission guide is just informational
        } else if (this.currentStep === 3) {
            // For step 3, check basic required fields without showing errors
            nextBtn.disabled = !this.isBasicFormValid();
        }
    }

    isBasicFormValid() {
        const cloudName = document.getElementById('cloud-name')?.value?.trim();
        const accountId = document.getElementById('account-id')?.value?.trim();
        const region = document.getElementById('primary-region')?.value?.trim();
        const email = document.getElementById('contact-email')?.value?.trim();

        // Basic required fields
        if (!cloudName || !accountId || !region || !email) {
            return false;
        }

        // Connection type specific validation
        if (this.selectedMethod === 'role') {
            const roleArn = document.getElementById('role-arn')?.value?.trim();
            return !!roleArn;
        } else if (this.selectedMethod === 'access_key') {
            const accessKey = document.getElementById('access-key')?.value?.trim();
            const secretKey = document.getElementById('secret-key')?.value?.trim();
            return !!(accessKey && secretKey);
        }

        return false;
    }

    previousStep() {
        // 수정 모드에서는 3단계 이전으로 갈 수 없음
        if (this.isEditMode && this.currentStep <= 3) {
            return;
        }

        if (this.currentStep > 1) {
            this.currentStep--;
            this.updateStepDisplay();
        }
    }

    nextStep() {
        if (this.currentStep < this.totalSteps) {
            if (this.validateCurrentStep()) {
                if (this.currentStep === 1) {
                    this.updatePermissionGuide();
                } else if (this.currentStep === 2) {
                    this.updateConnectionFields();
                } else if (this.currentStep === 3) {
                    this.collectFormData();
                    this.updateTestSection();
                }

                this.currentStep++;
                this.updateStepDisplay();
            }
        }
    }

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                return this.selectedMethod !== null;
            case 2:
                return true; // Permission guide is informational
            case 3:
                return this.validateFormData();
            case 4:
                return true; // Test step
            default:
                return false;
        }
    }

    updatePermissionGuide() {
        const roleGuide = document.getElementById('role-guide');
        const accessKeyGuide = document.getElementById('access-key-guide');

        if (this.selectedMethod === 'role') {
            roleGuide.classList.remove('hidden');
            accessKeyGuide.classList.add('hidden');
        } else {
            roleGuide.classList.add('hidden');
            accessKeyGuide.classList.remove('hidden');
        }

        // Generate random external ID for role method
        if (this.selectedMethod === 'role') {
            const externalId = 'WALB-' + Math.random().toString(36).substr(2, 9);
            // Load actual policies from server
            this.loadPolicies();
        }
    }

    async loadPolicies() {
        try {
            const response = await fetch('/connection/policies', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();

            if (data.success) {
                // Update Trust Policy
                const trustPolicyElement = document.getElementById('trust-policy-json');
                if (trustPolicyElement) {
                    trustPolicyElement.textContent = JSON.stringify(data.trust_policy, null, 2);
                }

                // Store external ID for form submission
                this.generatedExternalId = data.external_id;

                // Update any external ID display elements
                const externalIdElements = document.querySelectorAll('[data-external-id]');
                externalIdElements.forEach((el) => {
                    el.textContent = data.external_id;
                });

                console.log('Policies loaded successfully');
            } else {
                console.error('Failed to load policies:', data.error);
            }
        } catch (error) {
            console.error('Error loading policies:', error);
        }
    }

    setupFieldValidation() {
        // 실시간 입력 검증을 위한 이벤트 리스너 설정
        const fieldsToValidate = [
            { id: 'account-id', type: 'account_id' },
            { id: 'role-arn', type: 'role_arn' },
            { id: 'access-key-id', type: 'access_key' },
            { id: 'secret-access-key', type: 'secret_key' },
            { id: 'contact-email', type: 'email' },
        ];

        fieldsToValidate.forEach((field) => {
            const element = document.getElementById(field.id);
            if (element) {
                element.addEventListener('blur', () => this.validateField(field.type, element.value));
                element.addEventListener('input', () => this.clearFieldError(field.id));
            }
        });
    }

    async validateField(fieldType, value) {
        if (!value.trim()) return true; // 빈 값은 검증하지 않음

        try {
            const response = await fetch('/connection/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    field_type: fieldType,
                    value: value.trim(),
                }),
            });

            const data = await response.json();

            if (data.success) {
                if (data.is_valid) {
                    this.showFieldSuccess(fieldType, data.message);
                    return true;
                } else {
                    this.showFieldError(fieldType, data.message);
                    return false;
                }
            } else {
                console.error('Validation error:', data.error);
                return false;
            }
        } catch (error) {
            console.error('Field validation error:', error);
            return false;
        }
    }

    showFieldError(fieldType, message) {
        const fieldMap = {
            account_id: 'account-id',
            role_arn: 'role-arn',
            access_key: 'access-key-id',
            secret_key: 'secret-access-key',
            email: 'contact-email',
        };

        const fieldId = fieldMap[fieldType] || fieldType;
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.add('border-red-500', 'bg-red-50');
            field.classList.remove('border-green-500', 'bg-green-50');

            // 기존 에러 메시지 제거
            this.clearFieldError(fieldId);

            // 새 에러 메시지 추가
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-red-600 text-xs mt-1';
            errorDiv.textContent = message;
            field.parentNode.appendChild(errorDiv);
        }
    }

    showFieldSuccess(fieldType, message) {
        const fieldMap = {
            account_id: 'account-id',
            role_arn: 'role-arn',
            access_key: 'access-key-id',
            secret_key: 'secret-access-key',
            email: 'contact-email',
        };

        const fieldId = fieldMap[fieldType] || fieldType;
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.add('border-green-500', 'bg-green-50');
            field.classList.remove('border-red-500', 'bg-red-50');

            // 기존 메시지 제거
            this.clearFieldError(fieldId);
        }
    }

    clearFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.remove('border-red-500', 'bg-red-50', 'border-green-500', 'bg-green-50');

            // 에러 메시지 제거
            const errorMsg = field.parentNode.querySelector('.field-error');
            if (errorMsg) {
                errorMsg.remove();
            }
        }
    }

    handleFormInput(event) {
        this.validateCurrentStep();
        this.updateNextButton();

        // 계정 정보 요약 업데이트
        this.updateAccountSummary();
    }

    handleFormChange(event) {
        this.validateCurrentStep();
        this.updateNextButton();
        this.updateAccountSummary();
    }

    updateAccountSummary() {
        const summaryCard = document.getElementById('account-summary');
        if (!summaryCard) return;

        const cloudName = document.getElementById('cloud-name')?.value;
        const accountId = document.getElementById('account-id')?.value;
        const region = document.getElementById('primary-region')?.value;

        if (cloudName || accountId) {
            summaryCard.classList.remove('hidden');

            document.getElementById('summary-cloud-name').textContent = cloudName || '-';
            document.getElementById('summary-account-id').textContent = accountId || '-';
            document.getElementById('summary-connection-type').textContent = this.selectedMethod === 'role' ? '🛡️ Cross-Account Role' : '🔑 Access Key';
            document.getElementById('summary-region').textContent = region || '-';
        } else {
            summaryCard.classList.add('hidden');
        }
    }

    updateConnectionFields() {
        const roleFields = document.getElementById('role-fields');
        const accessKeyFields = document.getElementById('access-key-fields');

        if (this.selectedMethod === 'role') {
            roleFields.classList.remove('hidden');
            accessKeyFields.classList.add('hidden');

            // Set required attributes
            document.getElementById('role-arn').required = true;
            document.getElementById('access-key').required = false;
            document.getElementById('secret-key').required = false;

            // Pre-fill external ID if generated
            if (this.generatedExternalId) {
                document.getElementById('external-id').value = this.generatedExternalId;
            }
        } else {
            roleFields.classList.add('hidden');
            accessKeyFields.classList.remove('hidden');

            // Set required attributes
            document.getElementById('role-arn').required = false;
            document.getElementById('access-key').required = true;
            document.getElementById('secret-key').required = true;
        }
    }

    validateFormData() {
        const form = document.getElementById('account-form');
        const formData = new FormData(form);

        // Basic validation
        const required = ['cloud_name', 'account_id', 'primary_region', 'contact_email'];

        if (this.selectedMethod === 'role') {
            required.push('role_arn');
        } else {
            required.push('access_key', 'secret_key');
        }

        for (const field of required) {
            const value = formData.get(field);
            if (!value || value.trim() === '') {
                this.showFieldError(field, `${this.getFieldLabel(field)}은(는) 필수 입력 항목입니다.`);
                return false;
            } else {
                this.clearFieldError(field);
            }
        }

        // Specific validations
        const accountId = formData.get('account_id');
        if (accountId && !/^\d{12}$/.test(accountId)) {
            this.showFieldError('account_id', 'AWS 계정 ID는 12자리 숫자여야 합니다.');
            return false;
        }

        const email = formData.get('contact_email');
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            this.showFieldError('contact_email', '올바른 이메일 형식을 입력해주세요.');
            return false;
        }

        const roleArn = formData.get('role_arn');
        if (roleArn && this.selectedMethod === 'role') {
            if (!AWS_UTILS.validateRoleArn(roleArn)) {
                this.showFieldError('role_arn', '올바른 Role ARN 형식을 입력해주세요.');
                return false;
            }
        }

        return true;
    }

    showFieldError(fieldName, message) {
        const field = document.getElementById(fieldName.replace('_', '-'));
        if (field) {
            field.classList.add('border-red-500');

            // Remove existing error message
            const existingError = field.parentNode.querySelector('.error-message');
            if (existingError) {
                existingError.remove();
            }

            // Add error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            field.parentNode.appendChild(errorDiv);
        }
    }

    clearFieldError(fieldName) {
        const field = document.getElementById(fieldName.replace('_', '-'));
        if (field) {
            field.classList.remove('border-red-500');

            const errorMessage = field.parentNode.querySelector('.error-message');
            if (errorMessage) {
                errorMessage.remove();
            }
        }
    }

    getFieldLabel(fieldName) {
        const labels = {
            cloud_name: '클라우드 이름',
            account_id: 'AWS 계정 ID',
            primary_region: '기본 리전',
            contact_email: '담당자 이메일',
            role_arn: 'Role ARN',
            access_key: 'Access Key ID',
            secret_key: 'Secret Access Key',
        };
        return labels[fieldName] || fieldName;
    }

    collectFormData() {
        const form = document.getElementById('account-form');
        const formData = new FormData(form);

        this.formData = {
            cloud_name: formData.get('cloud_name'),
            account_id: formData.get('account_id'),
            primary_region: formData.get('primary_region'),
            contact_email: formData.get('contact_email'),
            connection_type: this.selectedMethod,
            created_at: new Date().toISOString(),
        };

        if (this.selectedMethod === 'role') {
            this.formData.role_arn = formData.get('role_arn');
            this.formData.external_id = formData.get('external_id');
        } else {
            // 백엔드에서 기대하는 필드명으로 매핑
            this.formData.access_key_id = formData.get('access_key');
            this.formData.secret_access_key = formData.get('secret_key');
        }

        // 디버깅용 콘솔 로그
        console.log('Collected form data:', this.formData);
        console.log('Selected method:', this.selectedMethod);
        console.log('Access key from form:', formData.get('access_key'));
        console.log('Secret key from form:', formData.get('secret_key'));
    }

    updateTestSection() {
        // Reset test section
        document.getElementById('test-waiting').classList.remove('hidden');
        document.getElementById('test-progress').classList.add('hidden');
        document.getElementById('test-result').classList.add('hidden');

        // Update test summary card
        this.updateTestSummary();
    }

    updateTestSummary() {
        // 기본 정보 업데이트
        document.getElementById('test-summary-cloud-name').textContent = document.getElementById('cloud-name')?.value || '-';
        document.getElementById('test-summary-account-id').textContent = document.getElementById('account-id')?.value || '-';
        document.getElementById('test-summary-region').textContent = document.getElementById('primary-region')?.value || '-';
        document.getElementById('test-summary-email').textContent = document.getElementById('contact-email')?.value || '-';

        // 연결 방식 정보 업데이트
        const connectionTypeElement = document.getElementById('test-summary-connection-type');
        const roleInfoElement = document.getElementById('test-summary-role-info');
        const keyInfoElement = document.getElementById('test-summary-key-info');

        if (this.selectedMethod === 'role') {
            connectionTypeElement.textContent = '🛡️ Cross-Account Role';
            roleInfoElement.classList.remove('hidden');
            keyInfoElement.classList.add('hidden');

            // Role 정보 업데이트
            document.getElementById('test-summary-role-arn').textContent = document.getElementById('role-arn')?.value || '-';
            document.getElementById('test-summary-external-id').textContent = document.getElementById('external-id')?.value || '-';
        } else if (this.selectedMethod === 'access_key') {
            connectionTypeElement.textContent = '🔑 Access Key';
            roleInfoElement.classList.add('hidden');
            keyInfoElement.classList.remove('hidden');

            // Access Key 정보 업데이트 (마스킹)
            const accessKey = document.getElementById('access-key')?.value || '-';
            document.getElementById('test-summary-access-key').textContent = accessKey.length > 4 ? accessKey.substring(0, 4) + '****' + accessKey.substring(accessKey.length - 4) : accessKey;
        }
    }

    async testConnection() {
        const testWaiting = document.getElementById('test-waiting');
        const testProgress = document.getElementById('test-progress');
        const testResult = document.getElementById('test-result');
        const testSuccess = document.getElementById('test-success');
        const testFailure = document.getElementById('test-failure');

        // Show progress
        testWaiting.classList.add('hidden');
        testProgress.classList.remove('hidden');
        testResult.classList.add('hidden');

        try {
            const result = await WALB.api.post('/connection/test', this.formData);

            // Hide progress
            testProgress.classList.add('hidden');
            testResult.classList.remove('hidden');

            if (result.success) {
                // Show success section and hide failure
                testSuccess.classList.remove('hidden');
                testFailure.classList.add('hidden');

                // Update success information
                document.getElementById('result-account-id').textContent = result.account_info?.account_id || this.formData.account_id;

                document.getElementById('result-regions').textContent = result.account_info?.available_regions?.length ? result.account_info.available_regions.length + '개 리전' : '1개 리전';

                document.getElementById('result-connection-time').textContent = result.account_info?.connection_time || '< 1초';

                // Update service test results table
                this.updateServiceTestResults(result.service_tests || {});

                // Enable save button
                const saveBtn = document.getElementById('save-btn');
                if (saveBtn) saveBtn.disabled = false;

                WALB.toast.show('AWS 연결 테스트가 성공했습니다!', 'success');
            } else {
                // Show failure section and hide success
                testSuccess.classList.add('hidden');
                testFailure.classList.remove('hidden');

                // Update error information
                document.getElementById('error-message').textContent = result.error || '연결에 실패했습니다.';

                // Update solution suggestions based on error type
                this.updateErrorSolutions(result.error_type);

                // Disable save button
                const saveBtn = document.getElementById('save-btn');
                if (saveBtn) saveBtn.disabled = true;

                WALB.toast.show('AWS 연결 테스트가 실패했습니다.', 'error');
            }
        } catch (error) {
            console.error('Connection test error:', error);

            testProgress.classList.add('hidden');
            testResult.classList.remove('hidden');

            // Show failure section for errors
            testSuccess.classList.add('hidden');
            testFailure.classList.remove('hidden');

            document.getElementById('error-message').textContent = error.message || '연결 테스트 중 예기치 않은 오류가 발생했습니다.';

            this.updateErrorSolutions('network_error');

            WALB.toast.show('연결 테스트 중 오류가 발생했습니다.', 'error');
        }
    }

    updateServiceTestResults(serviceTests) {
        const tableBody = document.getElementById('service-test-table-body');
        if (!tableBody) return;

        // Clear existing rows
        tableBody.innerHTML = '';

        // Default services to test (SHIELDUS 41개 체커 기준)
        const defaultServices = [
            // 핵심 서비스 (높은 사용 빈도)
            { name: 'IAM', key: 'iam', description: '사용자 및 권한 관리' },
            { name: 'EC2', key: 'ec2', description: '가상 서버 인스턴스' },
            { name: 'RDS', key: 'rds', description: '관계형 데이터베이스' },
            { name: 'S3', key: 's3', description: '객체 스토리지' },
            { name: 'CloudTrail', key: 'cloudtrail', description: '감사 로그' },
            { name: 'CloudWatch', key: 'cloudwatch', description: '모니터링 및 로그' },
            { name: 'KMS', key: 'kms', description: '암호화 키 관리' },

            // 보조 서비스 (중간 사용 빈도)
            { name: 'VPC', key: 'vpc', description: '가상 네트워크' },
            { name: 'ELB', key: 'elbv2', description: '로드 밸런서' },
            { name: 'EKS', key: 'eks', description: '쿠버네티스 서비스' },
            { name: 'Config', key: 'config', description: '구성 관리' },
            { name: 'Backup', key: 'backup', description: '백업 서비스' },
        ];

        defaultServices.forEach((service) => {
            const testResult = serviceTests[service.key] || { status: 'success', message: '접근 가능', response_time: '< 100ms' };
            const statusClass = testResult.status === 'success' ? 'status-success' : 'status-failed';
            const statusIcon = testResult.status === 'success' ? '✅' : '❌';
            const statusText = testResult.status === 'success' ? '허용됨' : '거부됨';
            const responseTime = testResult.response_time || (testResult.status === 'success' ? '< 100ms' : 'N/A');

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${service.name}</td>
                <td class="${statusClass}">${statusIcon} ${statusText}</td>
                <td>${service.description}</td>
                <td>${responseTime}</td>
            `;

            tableBody.appendChild(row);
        });
    }

    updateErrorSolutions(errorType) {
        const solutionElement = document.getElementById('error-solution');
        if (!solutionElement) return;

        const solutions = {
            invalid_credentials: ['AWS 자격증명(Access Key/Secret Key)이 올바른지 확인하세요', 'Role ARN이 정확한지 확인하세요', 'External ID가 일치하는지 확인하세요'],
            insufficient_permissions: ['IAM 권한이 적절히 설정되었는지 확인하세요', 'AdministratorAccess 정책이 연결되었는지 확인하세요', 'Cross-Account Role의 Trust Policy를 확인하세요'],
            network_error: ['네트워크 연결 상태를 확인하세요', '방화벽 설정을 확인하세요', 'AWS 서비스 상태를 확인하세요'],
            role_error: ['Role ARN이 존재하는지 확인하세요', 'Cross-Account Trust 관계가 설정되었는지 확인하세요', 'External ID가 정확한지 확인하세요'],
        };

        const errorSolutions = solutions[errorType] || solutions['invalid_credentials'];

        solutionElement.innerHTML = `
            <ul class="list-disc list-inside space-y-1">
                ${errorSolutions.map((solution) => `<li>${solution}</li>`).join('')}
            </ul>
        `;
    }

    async saveAccount() {
        const saveBtn = document.getElementById('save-btn');
        const originalText = saveBtn.textContent;

        WALB.loading.show(saveBtn);

        try {
            // 수정 모드인 경우 업데이트 API 사용
            const endpoint = this.isEditMode ? '/connection/update' : '/connection/save';
            const data = this.isEditMode ? { ...this.formData, original_account_id: this.editAccount.account_id } : this.formData;

            const result = await WALB.api.post(endpoint, data);

            if (result.success) {
                const message = this.isEditMode ? 'AWS 계정 정보가 성공적으로 수정되었습니다!' : 'AWS 계정이 성공적으로 저장되었습니다!';

                WALB.toast.show(message, 'success');

                // Redirect to main page after a short delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                WALB.loading.hide(saveBtn, originalText);
                WALB.toast.show(result.error || `계정 ${this.isEditMode ? '수정' : '저장'}에 실패했습니다.`, 'error');
            }
        } catch (error) {
            console.error('Save account error:', error);
            WALB.loading.hide(saveBtn, originalText);
            WALB.toast.show(`계정 ${this.isEditMode ? '수정' : '저장'} 중 오류가 발생했습니다.`, 'error');
        }
    }
}

// Global instance for access from HTML
window.connectionManager = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    window.connectionManager = new ConnectionManager();
    console.log('ConnectionManager 초기화 완료');
});
