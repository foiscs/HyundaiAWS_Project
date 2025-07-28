# AI Coding Agent Instructions

This is a multi-component AWS security management project with Korean output requirements.

## Architecture Overview

### Three Main Components (Work Boundaries)

1. **walb-flask/** - Primary development area (Flask web UI for integrated security management)
2. **SHIELDUS-AWS-CHECKER/** - Team-managed (security scanner, do not modify)
3. **WALB/** - Team-managed (Terraform infrastructure, do not modify)

**CRITICAL**: Work primarily in `walb-flask/` directory. Other directories are team-managed.

### Core Data Flow

```
AWS Account → Connection System (4-step onboarding) → Diagnosis System (41 checks) → Results/Remediation
```

## Development Context

**Environment**: Python 3.9.0, Flask 2.3.3, Korean UI language
**Primary workspace**: `walb-flask/` directory
**Account storage**: `registered_accounts.json` (one JSON object per line)

## Essential Flask Architecture Patterns

### Modular File Structure (5-6 files per feature)

**Connection System** (4 files):

-   `pages/connection.py` - Entry point controller
-   `connection_ui.py` - Unified UI class (800 lines)
-   `connection_engine.py` - Pure business logic engine
-   `connection_config.py` - Configuration constants
-   `connection_templates.py` - HTML templates
-   `connection_styles.py` - CSS styles

**Diagnosis System** (6 files):

-   `pages/diagnosis.py` - Entry point controller
-   `diagnosis_ui.py` - Unified UI class (520 lines)
-   `diagnosis_engine.py` - Core business logic (170 lines)
-   Similar config/templates/styles pattern

**Key Pattern**: Complete separation of concerns - UI/Business/Data/Templates/Styles never mix.

### Security Checker Implementation

**Base Pattern**: All checkers inherit from `BaseChecker` class:

```python
class BaseChecker:
    def run_diagnosis(self):  # Original check() logic
    def execute_fix(self):    # Original fix() logic
    def _get_manual_guide(self): # Web UI manual steps
```

**Critical Rule**: Preserve ALL original SHIELDUS-AWS-CHECKER messages, warnings, and manual procedures exactly. No engineering improvements or feature additions.

**Manual Guide System**: When automation is dangerous/impossible, implement `_get_manual_guide()` with web-friendly step-by-step instructions.

## Current Implementation Status

**Completed**: 16/41 security checkers

-   Account Management: 13/13 (1.1-1.13)
-   Authorization: 3/3 (2.1-2.3)

**Remaining**: 25 checkers need Flask implementation

-   Virtual Resources: 0/10 (3.1-3.10)
-   Operations: 0/15 (4.1-4.15)

## Development Commands

```bash
# Flask development
cd walb-flask
python run.py  # Starts on http://127.0.0.1:5000

# Security checker testing (original)
cd SHIELDUS-AWS-CHECKER
python main.py  # Full scan
python -c "from operation.4_1_ebs_encryption import check; print(check())"  # Individual check
```

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

**Account Registry**: `registered_accounts.json` - newline-delimited JSON objects
**Checker Mapping**: `diagnosis_service.py` contains `checker_mapping` dictionary
**AWS Session**: `session_manager.py` handles connection state across requests
**Shared Components**: `aws_handler.py` eliminates code duplication between systems

## Testing Approach

**No automated framework** - Manual testing via:

-   Flask: `python run.py` → browser workflow testing
-   Individual checkers: Import and call directly
-   AWS connectivity: Use built-in validation methods

## Security & Compliance Notes

-   SK Shieldus 41-item compliance checklist drives all functionality
-   EKS checks require VPC-internal access (kubectl commands)
-   Policy changes are manual-only due to operational risk
-   All Terraform modules include encryption by default
-   Log outputs sanitized to prevent credential exposure
