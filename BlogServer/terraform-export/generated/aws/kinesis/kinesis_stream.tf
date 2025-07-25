resource "aws_kinesis_stream" "tfer--cloudtrail-stream" {
  arn              = "arn:aws:kinesis:ap-northeast-2:253157413163:stream/cloudtrail-stream"
  encryption_type  = "NONE"
  name             = "cloudtrail-stream"
  retention_period = "24"
  shard_count      = "2"

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

resource "aws_kinesis_stream" "tfer--guardduty-stream" {
  arn              = "arn:aws:kinesis:ap-northeast-2:253157413163:stream/guardduty-stream"
  encryption_type  = "NONE"
  name             = "guardduty-stream"
  retention_period = "24"
  shard_count      = "1"

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}

resource "aws_kinesis_stream" "tfer--security-hub-stream" {
  arn              = "arn:aws:kinesis:ap-northeast-2:253157413163:stream/security-hub-stream"
  encryption_type  = "NONE"
  name             = "security-hub-stream"
  retention_period = "24"
  shard_count      = "1"

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}
