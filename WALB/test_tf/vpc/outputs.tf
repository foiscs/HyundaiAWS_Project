# VPC Module Outputs
# terraform-aws-modules/vpc/aws와 호환되는 출력값 정의

# VPC 정보
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.this.id
}

output "vpc_arn" {
  description = "VPC ARN"
  value       = aws_vpc.this.arn
}

output "vpc_cidr_block" {
  description = "VPC CIDR block"
  value       = aws_vpc.this.cidr_block
}

output "default_security_group_id" {
  description = "Default security group ID"
  value       = aws_vpc.this.default_security_group_id
}

output "default_network_acl_id" {
  description = "Default network ACL ID"
  value       = aws_vpc.this.default_network_acl_id
}

output "default_route_table_id" {
  description = "Default route table ID"
  value       = aws_vpc.this.default_route_table_id
}

output "vpc_main_route_table_id" {
  description = "Main route table ID"
  value       = aws_vpc.this.main_route_table_id
}

# Internet Gateway
output "igw_id" {
  description = "Internet Gateway ID"
  value       = try(aws_internet_gateway.this[0].id, "")
}

output "igw_arn" {
  description = "Internet Gateway ARN"
  value       = try(aws_internet_gateway.this[0].arn, "")
}

# Public Subnets
output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "public_subnet_arns" {
  description = "List of ARNs of public subnets"
  value       = aws_subnet.public[*].arn
}

output "public_subnets_cidr_blocks" {
  description = "List of CIDR blocks of public subnets"
  value       = aws_subnet.public[*].cidr_block
}

# Private Subnets
output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "private_subnet_arns" {
  description = "List of ARNs of private subnets"
  value       = aws_subnet.private[*].arn
}

output "private_subnets_cidr_blocks" {
  description = "List of CIDR blocks of private subnets"
  value       = aws_subnet.private[*].cidr_block
}

# NAT Gateways
output "nat_ids" {
  description = "List of IDs of NAT Gateways"
  value       = aws_nat_gateway.this[*].id
}

output "nat_public_ips" {
  description = "List of public Elastic IPs created for AWS NAT Gateway"
  value       = aws_eip.nat[*].public_ip
}

output "natgw_ids" {
  description = "List of IDs of NAT Gateways"
  value       = aws_nat_gateway.this[*].id
}

# Route Tables
output "public_route_table_ids" {
  description = "List of IDs of public route tables"
  value       = [aws_route_table.public.id]
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables"
  value       = aws_route_table.private[*].id
}

# Availability Zones
output "azs" {
  description = "List of availability zones"
  value       = var.azs
}