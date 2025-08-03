# check_role.ps1

param (
    [string]$role_name
)

if (-not $role_name) {
    Write-Output '{"error": "Role name is required"}'
    exit 1
}

# AWS CLI 실행 및 종료 코드 확인
$role_info_json = aws iam get-role --role-name $role_name --output json 2>$null
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0 -and $role_info_json) {
    $role_obj = $role_info_json | ConvertFrom-Json
    $arn = $role_obj.Role.Arn
    $result = @{
        exists = "true"
        role_name = $role_name
        arn = $arn
    } | ConvertTo-Json -Compress
    Write-Output $result
} else {
    $result = @{
        exists = "false"
        role_name = $role_name
    } | ConvertTo-Json -Compress
    Write-Output $result
}