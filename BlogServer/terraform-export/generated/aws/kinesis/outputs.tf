output "aws_kinesis_stream_tfer--cloudtrail-stream_id" {
  value = "${aws_kinesis_stream.tfer--cloudtrail-stream.id}"
}

output "aws_kinesis_stream_tfer--guardduty-stream_id" {
  value = "${aws_kinesis_stream.tfer--guardduty-stream.id}"
}

output "aws_kinesis_stream_tfer--security-hub-stream_id" {
  value = "${aws_kinesis_stream.tfer--security-hub-stream.id}"
}
