#!/bin/bash

# IAM 정책 존재 여부 확인 스크립트
policy_name="$1"

if [ -z "$policy_name" ]; then
    echo '{"error": "Policy name is required"}'
    exit 1
fi

# AWS CLI를 사용해서 정책 존재 여부 확인
account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$account_id" ]; then
    echo '{"error": "Unable to get AWS account ID"}'
    exit 1
fi

policy_arn="arn:aws:iam::${account_id}:policy/${policy_name}"

if aws iam get-policy --policy-arn "$policy_arn" >/dev/null 2>&1; then
    echo "{\"exists\": \"true\", \"policy_name\": \"$policy_name\", \"policy_arn\": \"$policy_arn\"}"
else
    echo "{\"exists\": \"false\", \"policy_name\": \"$policy_name\", \"policy_arn\": \"$policy_arn\"}"
fi