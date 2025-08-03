# check_user.ps1

param (
    [string]$user_name
)

if (-not $user_name) {
    Write-Output '{"error": "User name is required"}'
    exit 1
}

# AWS CLI 실행 및 종료 코드 확인
$user_info_json = aws iam get-user --user-name $user_name --output json 2>$null
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0 -and $user_info_json) {
    $user_obj = $user_info_json | ConvertFrom-Json
    $arn = $user_obj.User.Arn
    $result = @{
        exists = "true"
        user_name = $user_name
        arn = $arn
    } | ConvertTo-Json -Compress
    Write-Output $result
} else {
    $result = @{
        exists = "false"
        user_name = $user_name
    } | ConvertTo-Json -Compress
    Write-Output $result
}