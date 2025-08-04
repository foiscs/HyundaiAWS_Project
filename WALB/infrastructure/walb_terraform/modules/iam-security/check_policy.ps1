# check_policy.ps1

param ([string]$policy_name)

if (-not $policy_name) {
    Write-Output '{"error": "Policy name is required"}'
    exit 1
}

# AWS Account ID 가져오기 (통합된 방식)
$caller_identity_json = aws sts get-caller-identity --output json 2>$null
$account_exitCode = $LASTEXITCODE

if ($account_exitCode -ne 0 -or -not $caller_identity_json) {
    Write-Output '{"error": "Unable to get AWS account ID"}'
    exit 1
}

$caller_identity = $caller_identity_json | ConvertFrom-Json
$account_id = $caller_identity.Account
$policy_arn = "arn:aws:iam::${account_id}:policy/${policy_name}"

# AWS CLI 실행 및 종료 코드 확인
$policy_info_json = aws iam get-policy --policy-arn $policy_arn --output json 2>$null
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0 -and $policy_info_json) {
    $result = @{
        exists = "true"
        policy_name = $policy_name
        policy_arn = $policy_arn
    } | ConvertTo-Json -Compress
    Write-Output $result
} else {
    $result = @{
        exists = "false"
        policy_name = $policy_name
        policy_arn = $policy_arn
    } | ConvertTo-Json -Compress
    Write-Output $result
}