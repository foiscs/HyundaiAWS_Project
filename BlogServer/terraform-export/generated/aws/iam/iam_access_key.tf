resource "aws_iam_access_key" "tfer--AKIATV4K3SEVRGWVFPDJ" {
  depends_on = ["aws_iam_user.tfer--AIDATV4K3SEVTZLHC7OSN"]
  status     = "Active"
  user       = "blog-s3-user"
}

resource "aws_iam_access_key" "tfer--AKIATV4K3SEVT3X2PZ6C" {
  depends_on = ["aws_iam_user.tfer--AIDATV4K3SEVSTUEOG2TM"]
  status     = "Active"
  user       = "k8s"
}

resource "aws_iam_access_key" "tfer--AKIATV4K3SEVT52CYZNC" {
  depends_on = ["aws_iam_user.tfer--AIDATV4K3SEVV35MHA65O"]
  status     = "Active"
  user       = "test_user"
}

resource "aws_iam_access_key" "tfer--AKIATV4K3SEVTRB3OKXT" {
  depends_on = ["aws_iam_user.tfer--AIDATV4K3SEVWXQRO6LBF"]
  status     = "Active"
  user       = "admin"
}

resource "aws_iam_access_key" "tfer--AKIATV4K3SEVUAG3ZO3S" {
  depends_on = ["aws_iam_user.tfer--AIDATV4K3SEV4NCLENORQ"]
  status     = "Active"
  user       = "github-actions-deploy-user"
}

resource "aws_iam_access_key" "tfer--AKIATV4K3SEVW677O2UM" {
  depends_on = ["aws_iam_user.tfer--AIDATV4K3SEVWJDKGYNB6"]
  status     = "Active"
  user       = "splunk_addon"
}

resource "aws_iam_access_key" "tfer--AKIATV4K3SEVZFNDN7UE" {
  depends_on = ["aws_iam_user.tfer--AIDATV4K3SEV72ZRYCC5M"]
  status     = "Active"
  user       = "splunk-kinesis-reader"
}
