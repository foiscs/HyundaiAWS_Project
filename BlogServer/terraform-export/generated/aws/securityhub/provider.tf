provider "aws" {
  region = "ap-northeast-2"
}

terraform {
	required_providers {
		aws = {
	    version = "~> 5.100.0"
		}
  }
}
