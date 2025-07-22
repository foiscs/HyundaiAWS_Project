import boto3
import botocore
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
import logging
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AWSClientManager:
    """Manages AWS clients and sessions for security checking"""

    def __init__(self, region: str = 'ap-northeast-2', profile: Optional[str] = None):
        self.region = region
        self.profile = profile
        self.session = None
        self.clients = {}
        self._initialize_session()

    def _initialize_session(self):
        """Initialize AWS session with credentials"""
        try:
            if self.profile:
                self.session = boto3.Session(profile_name=self.profile, region_name=self.region)
            else:
                self.session = boto3.Session(region_name=self.region)

            # Test credentials
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            logger.info(f"AWS session initialized for account: {identity['Account']}")

        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"AWS credentials not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AWS session: {e}")
            raise

    def get_client(self, service_name: str) -> boto3.client:
        """Get or create AWS service client"""
        if service_name not in self.clients:
            try:
                self.clients[service_name] = self.session.client(service_name)
                logger.debug(f"Created {service_name} client")
            except Exception as e:
                logger.error(f"Failed to create {service_name} client: {e}")
                raise

        return self.clients[service_name]

    def get_account_id(self) -> str:
        """Get current AWS account ID"""
        try:
            sts_client = self.get_client('sts')
            return sts_client.get_caller_identity()['Account']
        except Exception as e:
            logger.error(f"Failed to get account ID: {e}")
            raise

    def get_region(self) -> str:
        """Get current AWS region"""
        return self.region

    def validate_credentials(self) -> bool:
        """Validate AWS credentials"""
        try:
            sts_client = self.get_client('sts')
            sts_client.get_caller_identity()
            return True
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return False

    def list_available_regions(self, service_name: str = 'ec2') -> List[str]:
        """List available regions for a service"""
        try:
            client = self.get_client(service_name)
            regions = client.describe_regions()['Regions']
            return [region['RegionName'] for region in regions]
        except Exception as e:
            logger.error(f"Failed to list regions: {e}")
            return []

class AWSServiceChecker:
    """Utility class for checking AWS service availability and limits"""

    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager

    def check_service_availability(self, service_name: str) -> bool:
        """Check if AWS service is available in current region"""
        try:
            client = self.client_manager.get_client(service_name)
            # Try a simple operation to test service availability
            if service_name == 'iam':
                client.list_users(MaxItems=1)
            elif service_name == 'ec2':
                client.describe_regions()
            elif service_name == 's3':
                client.list_buckets()
            elif service_name == 'rds':
                client.describe_db_instances(MaxRecords=1)
            elif service_name == 'eks':
                client.list_clusters(maxResults=1)
            else:
                # Generic test - try to get service client
                pass

            return True
        except Exception as e:
            logger.warning(f"Service {service_name} not available: {e}")
            return False

    def get_service_quotas(self, service_name: str) -> Dict[str, Any]:
        """Get service quotas for AWS service"""
        quotas = {}
        try:
            if service_name == 'iam':
                iam_client = self.client_manager.get_client('iam')
                # Get account summary for IAM limits
                summary = iam_client.get_account_summary()
                quotas = {
                    'users': summary.get('Users', 0),
                    'groups': summary.get('Groups', 0),
                    'roles': summary.get('Roles', 0),
                    'policies': summary.get('Policies', 0)
                }
            elif service_name == 'ec2':
                ec2_client = self.client_manager.get_client('ec2')
                # Get VPC and security group counts
                vpcs = ec2_client.describe_vpcs()['Vpcs']
                sgs = ec2_client.describe_security_groups()['SecurityGroups']
                quotas = {
                    'vpcs': len(vpcs),
                    'security_groups': len(sgs)
                }
            elif service_name == 's3':
                s3_client = self.client_manager.get_client('s3')
                buckets = s3_client.list_buckets()['Buckets']
                quotas = {
                    'buckets': len(buckets)
                }

        except Exception as e:
            logger.error(f"Failed to get quotas for {service_name}: {e}")

        return quotas

    def check_rate_limits(self, service_name: str) -> Dict[str, Any]:
        """Check current rate limiting status"""
        rate_info = {
            'service': service_name,
            'current_time': datetime.now().isoformat(),
            'throttled': False,
            'retry_after': None
        }

        try:
            client = self.client_manager.get_client(service_name)
            # Make a simple API call to check for throttling
            start_time = time.time()

            if service_name == 'iam':
                client.list_users(MaxItems=1)
            elif service_name == 'ec2':
                client.describe_instances(MaxResults=5)
            elif service_name == 's3':
                client.list_buckets()

            response_time = time.time() - start_time
            rate_info['response_time'] = response_time

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['Throttling', 'ThrottlingException', 'RequestLimitExceeded']:
                rate_info['throttled'] = True
                rate_info['error'] = str(e)
                # Extract retry-after if available
                if 'Retry-After' in e.response.get('ResponseMetadata', {}).get('HTTPHeaders', {}):
                    rate_info['retry_after'] = e.response['ResponseMetadata']['HTTPHeaders']['Retry-After']
        except Exception as e:
            logger.error(f"Rate limit check failed for {service_name}: {e}")
            rate_info['error'] = str(e)

        return rate_info

class AWSResourceCounter:
    """Count AWS resources for security assessment"""

    def __init__(self, client_manager: AWSClientManager):
        self.client_manager = client_manager

    def count_iam_resources(self) -> Dict[str, int]:
        """Count IAM resources"""
        counts = {}
        try:
            iam_client = self.client_manager.get_client('iam')

            # Count users
            paginator = iam_client.get_paginator('list_users')
            users = []
            for page in paginator.paginate():
                users.extend(page['Users'])
            counts['users'] = len(users)

            # Count groups
            paginator = iam_client.get_paginator('list_groups')
            groups = []
            for page in paginator.paginate():
                groups.extend(page['Groups'])
            counts['groups'] = len(groups)

            # Count roles
            paginator = iam_client.get_paginator('list_roles')
            roles = []
            for page in paginator.paginate():
                roles.extend(page['Roles'])
            counts['roles'] = len(roles)

            # Count policies
            paginator = iam_client.get_paginator('list_policies')
            policies = []
            for page in paginator.paginate(Scope='Local'):
                policies.extend(page['Policies'])
            counts['customer_managed_policies'] = len(policies)

        except Exception as e:
            logger.error(f"Failed to count IAM resources: {e}")

        return counts

    def count_ec2_resources(self) -> Dict[str, int]:
        """Count EC2 resources"""
        counts = {}
        try:
            ec2_client = self.client_manager.get_client('ec2')

            # Count instances
            paginator = ec2_client.get_paginator('describe_instances')
            instances = []
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    instances.extend(reservation['Instances'])
            counts['instances'] = len(instances)

            # Count security groups
            paginator = ec2_client.get_paginator('describe_security_groups')
            security_groups = []
            for page in paginator.paginate():
                security_groups.extend(page['SecurityGroups'])
            counts['security_groups'] = len(security_groups)

            # Count VPCs
            vpcs = ec2_client.describe_vpcs()['Vpcs']
            counts['vpcs'] = len(vpcs)

            # Count subnets
            subnets = ec2_client.describe_subnets()['Subnets']
            counts['subnets'] = len(subnets)

        except Exception as e:
            logger.error(f"Failed to count EC2 resources: {e}")

        return counts

    def count_s3_resources(self) -> Dict[str, int]:
        """Count S3 resources"""
        counts = {}
        try:
            s3_client = self.client_manager.get_client('s3')

            # Count buckets
            buckets = s3_client.list_buckets()['Buckets']
            counts['buckets'] = len(buckets)

            # Count objects in each bucket (sample)
            total_objects = 0
            for bucket in buckets[:5]:  # Limit to first 5 buckets to avoid long execution
                try:
                    paginator = s3_client.get_paginator('list_objects_v2')
                    object_count = 0
                    for page in paginator.paginate(Bucket=bucket['Name']):
                        object_count += page.get('KeyCount', 0)
                    total_objects += object_count
                except Exception as e:
                    logger.warning(f"Failed to count objects in bucket {bucket['Name']}: {e}")

            counts['sample_objects'] = total_objects

        except Exception as e:
            logger.error(f"Failed to count S3 resources: {e}")

        return counts
