#!/bin/bash

user_name="$1"

if [ -z "$user_name" ]; then
    echo '{"error": "User name is required"}'
    exit 1
fi

# AWS CLI로 User 존재 여부 및 ARN 확인
user_info=$(aws iam get-user --user-name "$user_name" --output json 2>/dev/null)
if [ $? -eq 0 ]; then
    arn=$(echo "$user_info" | jq -r '.User.Arn')
    echo "{\"exists\": \"true\", \"user_name\": \"$user_name\", \"arn\": \"$arn\"}"
else
    echo "{\"exists\": \"false\", \"user_name\": \"$user_name\"}"
fi