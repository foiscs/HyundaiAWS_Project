#!/bin/bash

# IAM Role 존재 여부 확인 스크립트
role_name="$1"

if [ -z "$role_name" ]; then
    echo '{"error": "Role name is required"}'
    exit 1
fi

# AWS CLI로 Role 존재 여부 및 ARN 확인
role_info=$(aws iam get-role --role-name "$role_name" --output json 2>/dev/null)
if [ $? -eq 0 ]; then
    arn=$(echo "$role_info" | jq -r '.Role.Arn')
    echo "{\"exists\": \"true\", \"role_name\": \"$role_name\", \"arn\": \"$arn\"}"
else
    echo "{\"exists\": \"false\", \"role_name\": \"$role_name\"}"
fi