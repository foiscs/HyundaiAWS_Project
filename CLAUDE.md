# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-component AWS security management project with three main components:
1. **SHIELDUS-AWS-CHECKER** - Automated AWS security compliance checker based on SK Shieldus cloud security guidelines
2. **mainHub** - Streamlit-based web UI for integrated security management platform (WALB)
3. **WALB** - Terraform infrastructure-as-code for secure AWS environment provisioning

## Development Environment

**Python Version**: 3.9.0

**Dependencies**: Install from root requirements.txt:
```bash
pip install -r requirements.txt
```

Required packages:
- streamlit>=1.28.0
- boto3>=1.20.0  
- botocore>=1.23.0
- python-dateutil>=2.8.2

## Common Development Commands

### SHIELDUS-AWS-CHECKER (Security Scanner)
```bash
# Navigate to checker directory
cd SHIELDUS-AWS-CHECKER

# Run full security check (requires AWS credentials)
python main.py

# Check specific module
python -c "from account_management.1_1_user_account import check; check()"
```

### mainHub (Streamlit Web UI)
```bash
# Navigate to mainHub directory  
cd mainHub

# Run the web application
streamlit run main.py

# Run specific page for development/testing
streamlit run pages/connection.py
streamlit run pages/diagnosis.py
```

### WALB (Terraform Infrastructure)
```bash
# Navigate to terraform directory
cd WALB/infrastructure/terraform

# Initialize terraform
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure (requires AWS credentials and terraform.tfvars)
terraform apply
```

## Code Architecture

### SHIELDUS-AWS-CHECKER Structure
- **main.py**: Orchestrates all security checks, loads modules dynamically from CHECK_MODULES dictionary
- **aws_client.py**: Centralized AWS client management with AWSClientManager, AWSServiceChecker, and AWSResourceCounter classes
- **account_management/**: IAM and user account security checks (13 modules)
- **authorization/**: Service policy and permission checks (3 modules) 
- **virtual_resources/**: Network and infrastructure security checks (10 modules)
- **operation/**: Encryption, logging, and operational security checks (15 modules)

Each security check module must implement:
- `check()` function that returns findings (truthy values indicate vulnerabilities)
- Optional `fix()` function for automated remediation

### mainHub (WALB Web Platform) Structure
- **main.py**: Main Streamlit application with account management dashboard
- **components/**: Reusable UI components and business logic
  - **session_manager.py**: Manages user sessions and state
  - **aws_handler.py**: AWS service integrations
  - **sk_diagnosis/**: Security diagnosis modules implementing BaseChecker abstract class
  - **connection_components.py**: AWS account connection utilities
- **pages/**: Streamlit page modules (connection.py, diagnosis.py)

Key patterns:
- BaseChecker abstract class in `components/sk_diagnosis/base_checker.py` defines interface for all diagnosis modules
- Account data stored in `registered_accounts.json` (one JSON object per line)
- Streamlit session state used for navigation and data persistence

### WALB Terraform Structure
- **main.tf**: Complete AWS infrastructure orchestration
- **modules/**: Modular infrastructure components (vpc, eks, rds, s3, dynamodb, ecr)
- **terraform.tfvars**: Environment-specific variable values
- **security.tf**: Centralized security configurations
- Follows security-first design with encryption, logging, and access controls built-in

## AWS Authentication

All components require valid AWS credentials. Configure via one of:
- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- IAM roles (when running on EC2/EKS)
- AWS profiles: Set profile name in connection configuration

## Testing and Validation

No automated test framework is currently configured. Manual testing approaches:

### SHIELDUS-AWS-CHECKER Testing
```bash
# Test individual security check modules
python -c "from operation.4_1_ebs_encryption import check; print(check())"

# Verify AWS client connectivity
python -c "from aws_client import AWSClientManager; mgr = AWSClientManager(); print(mgr.validate_credentials())"
```

### mainHub Testing
```bash
# Test Streamlit components locally
streamlit run main.py
# Navigate through connection and diagnosis workflows
```

### WALB Testing  
```bash
# Validate Terraform configuration
terraform validate

# Plan without applying changes
terraform plan -var-file="terraform.tfvars"
```

## Security Considerations

- Never commit AWS credentials, access keys, or sensitive data
- Use IAM roles and policies with minimal required permissions
- All Terraform modules include encryption by default
- Log outputs are sanitized to prevent credential exposure
- WALB follows ISMS-P compliance patterns

## Development Guidelines

**IMPORTANT**: Only work within the `mainHub/` directory. Other directories (`SHIELDUS-AWS-CHECKER/`, `WALB/`) are managed by team members and should not be modified.

## Project-Specific Notes

- SHIELDUS-AWS-CHECKER contains 41 security check items based on SK Shieldus guidelines
- Some checks (EKS-related) require manual verification with kubectl
- mainHub provides both UI-driven diagnosis and automated infrastructure provisioning
- Terraform modules are designed for production-ready secure deployments
- The codebase supports Korean language output for SK Shieldus integration