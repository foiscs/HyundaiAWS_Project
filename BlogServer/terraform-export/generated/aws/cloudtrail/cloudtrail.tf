resource "aws_cloudtrail" "tfer--test-cloudtrail-logs" {
  advanced_event_selector {
    field_selector {
      equals = ["AWS::Lambda::Function"]
      field  = "resources.type"
    }

    field_selector {
      equals = ["Data"]
      field  = "eventCategory"
    }
  }

  advanced_event_selector {
    field_selector {
      equals = ["AWS::S3::Object"]
      field  = "resources.type"
    }

    field_selector {
      equals = ["Data"]
      field  = "eventCategory"
    }
  }

  advanced_event_selector {
    field_selector {
      equals = ["AWS::DynamoDB::Table"]
      field  = "resources.type"
    }

    field_selector {
      equals = ["Data"]
      field  = "eventCategory"
    }
  }

  advanced_event_selector {
    field_selector {
      equals = ["Management"]
      field  = "eventCategory"
    }

    name = "관리 이벤트 선택기"
  }

  cloud_watch_logs_group_arn    = "arn:aws:logs:ap-northeast-2:253157413163:log-group:aws-cloudtrail-logs:*"
  cloud_watch_logs_role_arn     = "arn:aws:iam::253157413163:role/service-role/CloudTrail_CloudWatchLogs_Role"
  enable_log_file_validation    = "true"
  enable_logging                = "true"
  include_global_service_events = "true"
  is_multi_region_trail         = "true"
  is_organization_trail         = "false"
  kms_key_id                    = "arn:aws:kms:ap-northeast-2:253157413163:key/9ae015e0-ef91-4313-9192-1a5e9e6f0e46"
  name                          = "test-cloudtrail-logs"
  s3_bucket_name                = "team2-aws-logs-splunk"
  s3_key_prefix                 = "cloudtrail-logs"
}
