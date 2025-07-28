# AI Coding Agent Instructions

This is a multi-component AWS security management project with Korean output requirements.

## Architecture Overview

### Four Main Components (Work Boundaries)

1. **walb-flask/** - Primary Flask web application (MVC architecture, production-ready)
2. **mainHub/** - Legacy Streamlit prototype (reference only, not actively developed)
3. **SHIELDUS-AWS-CHECKER/** - Team-managed (security scanner, do not modify)
4. **WALB/** - Team-managed (Terraform infrastructure, do not modify)

**CRITICAL**: Work primarily in `walb-flask/` directory. Other directories are team-managed or legacy.

### Core Data Flow

```
AWS Account → Connection System (4-step onboarding) → Diagnosis System (41 checks) → Results/Remediation
```

## Development Context

**Environment**: Python 3.9.0, Flask 2.3.3, Korean UI language
**Primary workspace**: `walb-flask/` directory
**Account storage**: `walb-flask/data/registered_accounts.json` (newline-delimited JSON)

**CRITICAL**: Always activate micromamba environment before running any Python commands:

```bash
micromamba activate aws_pjt
```

**CRITICAL**: Always run Flask application from `walb-flask/` directory:

```bash
cd walb-flask
micromamba activate aws_pjt
python run.py
```

## Flask Architecture Patterns

### MVC Structure (Flask Best Practices)

**Core Application Structure**:

```
walb-flask/
├── app/
│   ├── __init__.py        # Application factory
│   ├── views/             # Controllers (Blueprints)
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   ├── checkers/          # Security check implementations
│   ├── utils/             # Shared utilities
│   └── config/            # Configuration classes
├── templates/             # Jinja2 templates
├── static/                # CSS/JS/assets
├── data/                  # JSON data files
└── logs/                  # Application logs
```

**Blueprint Pattern**: Each feature is a Flask Blueprint:

-   `app/views/main.py` → `main_bp`
-   `app/views/connection.py` → `connection_bp` (AWS account onboarding)
-   `app/views/diagnosis.py` → `diagnosis_bp` (security scanning)
-   `app/views/api.py` → `api_bp` (REST endpoints)
-   `app/views/monitoring.py` → `monitoring_bp` (system status)
-   `app/views/logs.py` → `logs_bp` (log viewer)

**Service Layer Pattern**: Business logic separated from controllers:

-   `app/services/diagnosis_service.py` - Core diagnosis engine
-   `app/models/account.py` - AWS account data management
-   `app/utils/aws_handler.py` - AWS SDK wrapper

### Security Checker Implementation

**Base Pattern**: All checkers inherit from `BaseChecker` class in `app/checkers/base_checker.py`:

```python
class BaseChecker(ABC):
    def run_diagnosis(self):     # Original check() logic from SHIELDUS-AWS-CHECKER
    def execute_fix(self):       # Original fix() logic from SHIELDUS-AWS-CHECKER
    def _get_manual_guide(self): # Web UI manual steps when automation is risky
```

**Checker Organization**: Mirrors SHIELDUS-AWS-CHECKER structure:

-   `app/checkers/account_management/` (1.1-1.13) - Complete ✓
-   `app/checkers/authorization/` (2.1-2.3) - Complete ✓
-   `app/checkers/virtual_resources/` (3.1-3.10) - In Progress
-   `app/checkers/operation/` (4.1-4.15) - In Progress

**Critical Rule**: Preserve ALL original SHIELDUS-AWS-CHECKER messages, warnings, and procedures exactly. Each checker file header contains reference to original source.

## Current Implementation Status

**Completed**: 16/41 security checkers migrated to Flask architecture

-   Account Management: 13/13 (1.1-1.13) ✓
-   Authorization: 3/3 (2.1-2.3) ✓

**In Progress**: 25 checkers being migrated from SHIELDUS-AWS-CHECKER

-   Virtual Resources: ~10/10 (3.1-3.10) - Active development
-   Operations: ~15/15 (4.1-4.15) - Active development

**Migration Pattern**: Each checker preserves original logic while adapting to Flask/web interface patterns.

## Development Commands

**CRITICAL**: Always activate micromamba environment before running any Python commands:

```bash
micromamba activate aws_pjt
```

````bash
# Flask development server
cd walb-flask
micromamba activate aws_pjt
python run.py  # Starts on http://127.0.0.1:5000

# Legacy Streamlit (mainHub) - Reference only
cd mainHub
micromamba activate aws_pjt
streamlit run main.py  # Port 8501, not actively developed

# Security checker testing (original)
cd SHIELDUS-AWS-CHECKER
micromamba activate aws_pjt
python main.py  # Full scan
python -c "from operation.4_1_ebs_encryption import check; print(check())"  # Individual check
```## Flask-Specific Patterns

**Template Structure**: Jinja2 templates in `templates/` with component-based organization
**Static Assets**: CSS/JS in `static/` directory with per-feature organization
**Error Handling**: Centralized error handling in Flask blueprints with Korean error messages
**Logging**: Structured logging in `logs/` directory with diagnosis-specific log files
**Configuration**: Environment-based config in `config.py` with development/production settings

## AWS Integration Patterns

**Dual Authentication**: Cross-Account Role (preferred) or Access Keys
**Session Management**: `aws_handler.py` provides centralized AWS client management
**Credential Security**: Never commit secrets, use IAM roles when possible

## UI/UX Implementation Rules

**Styling**: Tailwind CSS primary, custom CSS in `static/css/` per module
**JavaScript**: Vanilla JS with fetch API, no external libraries
**Responsive**: Mobile/desktop compatibility required
**Korean Output**: All user-facing text in Korean per SK Shieldus requirements

## Critical Integration Points

**Account Registry**: `walb-flask/data/registered_accounts.json` - newline-delimited JSON objects
**Checker Mapping**: `app/services/diagnosis_service.py` contains `checker_mapping` dictionary
**AWS Session**: `app/utils/aws_handler.py` handles connection state across requests
**Shared Components**: Flask blueprint pattern eliminates code duplication between features

## Testing Approach

**No automated framework** - Manual testing via:

-   Flask: `python run.py` → browser workflow testing
-   Individual checkers: Import and call directly
-   AWS connectivity: Use built-in validation methods

## Common Issues & Solutions

**Logging Problems**:
- Diagnosis logs save to `logs/diagnosis/` directory automatically
- Log file format: `YYYYMMDD_HHMMSS_AccountID.log` (timestamp + account ID)
- Log file path returned in diagnosis results under `log_file_path` key
- Session logs include full execution details with Korean messages
- Logs are written in real-time during 41-item diagnosis batch execution**Checker Implementation Issues**:
- `_get_manual_guide()` method signatures vary across checkers
- BaseChecker handles multiple signatures with try-except fallback
- Some checkers need no arguments, others need result data
- Manual guides only shown when `has_issues=True` (fixed)

**Flask Context Issues**:
- Always run tests with proper Flask application context
- Use `create_app()` and `with app.app_context():` for standalone scripts
-   AWS connectivity: Use built-in validation methods

## Security & Compliance Notes

-   SK Shieldus 41-item compliance checklist drives all functionality
-   EKS checks require VPC-internal access (kubectl commands)
-   Policy changes are manual-only due to operational risk
-   All Terraform modules include encryption by default
-   Log outputs sanitized to prevent credential exposure
````
