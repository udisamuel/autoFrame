import logging
import json
import allure
import boto3
import botocore.exceptions
from typing import Dict, Any, Optional, Union, List
from config.config import Config

logger = logging.getLogger(__name__)

class AWSHelper:
    """
    Helper class for AWS testing that provides enhanced functionality for AWS services.
    """
    
    def __init__(self, region_name: Optional[str] = None, profile_name: Optional[str] = None,
                 access_key_id: Optional[str] = None, secret_access_key: Optional[str] = None,
                 session_token: Optional[str] = None, endpoint_url: Optional[str] = None):
        """
        Initialize the AWS helper with optional AWS credentials.
        
        Args:
            region_name: AWS region name. Defaults to Config.AWS_REGION if not provided.
            profile_name: AWS profile name for credentials
            access_key_id: AWS access key ID. Defaults to Config.AWS_ACCESS_KEY_ID if not provided.
            secret_access_key: AWS secret access key. Defaults to Config.AWS_SECRET_ACCESS_KEY if not provided.
            session_token: AWS session token. Defaults to Config.AWS_SESSION_TOKEN if not provided.
            endpoint_url: Custom endpoint URL for testing with local AWS services like LocalStack
        """
        self.region_name = region_name or Config.AWS_REGION
        self.profile_name = profile_name
        self.access_key_id = access_key_id or Config.AWS_ACCESS_KEY_ID
        self.secret_access_key = secret_access_key or Config.AWS_SECRET_ACCESS_KEY
        self.session_token = session_token or Config.AWS_SESSION_TOKEN
        self.endpoint_url = endpoint_url or Config.AWS_ENDPOINT_URL
        
        self.session = self._create_session()
        self.clients = {}  # Dictionary to cache boto3 clients
        self.resources = {}  # Dictionary to cache boto3 resources
    
    def _create_session(self) -> boto3.Session:
        """
        Create a boto3 session with the configured credentials.
        
        Returns:
            A boto3 Session object
        """
        with allure.step("Creating AWS session"):
            try:
                # If profile_name is provided, use it first
                if self.profile_name:
                    logger.info(f"Creating AWS session with profile: {self.profile_name}")
                    session = boto3.Session(profile_name=self.profile_name, region_name=self.region_name)
                # Otherwise, try with explicit credentials if provided
                elif self.access_key_id and self.secret_access_key:
                    logger.info(f"Creating AWS session with explicit credentials in region: {self.region_name}")
                    session = boto3.Session(
                        aws_access_key_id=self.access_key_id,
                        aws_secret_access_key=self.secret_access_key,
                        aws_session_token=self.session_token,
                        region_name=self.region_name
                    )
                # Fall back to default credentials
                else:
                    logger.info(f"Creating AWS session with default credentials in region: {self.region_name}")
                    session = boto3.Session(region_name=self.region_name)
                
                return session
                
            except Exception as e:
                logger.exception(f"Failed to create AWS session: {str(e)}")
                allure.attach(
                    f"Failed to create AWS session: {str(e)}",
                    name="AWS Session Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def get_client(self, service_name: str) -> Any:
        """
        Get a boto3 client for the specified AWS service.
        
        Args:
            service_name: The name of the AWS service (e.g., 's3', 'ec2', 'dynamodb')
            
        Returns:
            A boto3 client for the specified service
        """
        # If we already have a client for this service, return it
        if service_name in self.clients:
            return self.clients[service_name]
        
        # Otherwise, create a new client
        with allure.step(f"Creating AWS client for {service_name}"):
            try:
                kwargs = {'service_name': service_name}
                if self.endpoint_url:
                    kwargs['endpoint_url'] = self.endpoint_url
                
                logger.info(f"Creating {service_name} client")
                client = self.session.client(**kwargs)
                
                # Cache the client for future use
                self.clients[service_name] = client
                
                return client
                
            except Exception as e:
                logger.exception(f"Failed to create {service_name} client: {str(e)}")
                allure.attach(
                    f"Failed to create {service_name} client: {str(e)}",
                    name="AWS Client Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def get_resource(self, service_name: str) -> Any:
        """
        Get a boto3 resource for the specified AWS service.
        
        Args:
            service_name: The name of the AWS service (e.g., 's3', 'ec2', 'dynamodb')
            
        Returns:
            A boto3 resource for the specified service
        """
        # If we already have a resource for this service, return it
        if service_name in self.resources:
            return self.resources[service_name]
        
        # Otherwise, create a new resource
        with allure.step(f"Creating AWS resource for {service_name}"):
            try:
                kwargs = {'service_name': service_name}
                if self.endpoint_url:
                    kwargs['endpoint_url'] = self.endpoint_url
                
                logger.info(f"Creating {service_name} resource")
                resource = self.session.resource(**kwargs)
                
                # Cache the resource for future use
                self.resources[service_name] = resource
                
                return resource
                
            except Exception as e:
                logger.exception(f"Failed to create {service_name} resource: {str(e)}")
                allure.attach(
                    f"Failed to create {service_name} resource: {str(e)}",
                    name="AWS Resource Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def execute_aws_action(self, service_name: str, action_name: str, 
                          use_client: bool = True, **kwargs) -> Any:
        """
        Execute an action on an AWS service.
        
        Args:
            service_name: The name of the AWS service (e.g., 's3', 'ec2', 'dynamodb')
            action_name: The name of the action to execute (e.g., 'list_buckets', 'describe_instances')
            use_client: Whether to use a client (True) or resource (False)
            **kwargs: Additional arguments to pass to the action
            
        Returns:
            The result of the action
        """
        with allure.step(f"AWS {service_name} - {action_name}"):
            try:
                # Get the appropriate service object (client or resource)
                service_obj = self.get_client(service_name) if use_client else self.get_resource(service_name)
                
                # Log the action
                self._log_aws_action(service_name, action_name, kwargs)
                
                # Execute the action
                action = getattr(service_obj, action_name)
                result = action(**kwargs)
                
                # Log the result
                self._log_aws_result(service_name, action_name, result)
                
                return result
                
            except AttributeError as e:
                error_message = f"Action '{action_name}' not found for {service_name}"
                logger.exception(error_message)
                allure.attach(
                    error_message,
                    name="AWS Action Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
                
            except botocore.exceptions.ClientError as e:
                error_message = f"AWS {service_name} {action_name} failed: {str(e)}"
                logger.exception(error_message)
                allure.attach(
                    error_message,
                    name="AWS Client Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
                
            except Exception as e:
                error_message = f"Unexpected error in AWS {service_name} {action_name}: {str(e)}"
                logger.exception(error_message)
                allure.attach(
                    error_message,
                    name="AWS Unexpected Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def _log_aws_action(self, service_name: str, action_name: str, kwargs: Dict[str, Any]) -> None:
        """
        Log an AWS action.
        
        Args:
            service_name: The name of the AWS service
            action_name: The name of the action
            kwargs: The arguments to the action
        """
        # Sanitize parameters to mask sensitive information
        sanitized_kwargs = self._sanitize_params(kwargs)
        
        logger.info(f"AWS {service_name} - {action_name}")
        logger.debug(f"Parameters: {sanitized_kwargs}")
        
        allure.attach(
            f"Service: {service_name}\n"
            f"Action: {action_name}\n"
            f"Parameters: {json.dumps(sanitized_kwargs, indent=2, default=str)}",
            name="AWS Action Details",
            attachment_type=allure.attachment_type.TEXT
        )
    
    def _log_aws_result(self, service_name: str, action_name: str, result: Any) -> None:
        """
        Log the result of an AWS action.
        
        Args:
            service_name: The name of the AWS service
            action_name: The name of the action
            result: The result of the action
        """
        # Handle response metadata for client responses
        if isinstance(result, dict) and 'ResponseMetadata' in result:
            status_code = result['ResponseMetadata'].get('HTTPStatusCode', 'N/A')
            request_id = result['ResponseMetadata'].get('RequestId', 'N/A')
            logger.info(f"AWS {service_name} - {action_name} - Status: {status_code} - RequestId: {request_id}")
            
            # Remove ResponseMetadata for cleaner logs
            result_to_log = result.copy()
            result_to_log.pop('ResponseMetadata', None)
        else:
            logger.info(f"AWS {service_name} - {action_name} - Completed")
            result_to_log = result
        
        # Format the result for logging - handle different types of results
        formatted_result = self._format_result_for_logging(result_to_log)
        
        logger.debug(f"Result: {formatted_result}")
        
        allure.attach(
            f"Service: {service_name}\n"
            f"Action: {action_name}\n"
            f"Result: {formatted_result}",
            name="AWS Action Result",
            attachment_type=allure.attachment_type.TEXT
        )
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize parameters to hide sensitive information.
        
        Args:
            params: The parameters for the AWS action
            
        Returns:
            The sanitized parameters
        """
        # List of parameter names that might indicate sensitive information
        sensitive_params = [
            'secret', 'password', 'passwd', 'token', 'key', 'auth', 'credential',
            'private', 'access_key', 'session', 'signature', 'ssn', 'ssm'
        ]
        
        sanitized = {}
        for key, value in params.items():
            # If the parameter name contains a sensitive term, mask it
            if any(sensitive in key.lower() for sensitive in sensitive_params):
                sanitized[key] = '********'
                
            # If the value is a dictionary, sanitize it recursively
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
                
            # Otherwise, keep it as is
            else:
                sanitized[key] = value
                
        return sanitized
    
    def _format_result_for_logging(self, result: Any) -> str:
        """
        Format a result for logging.
        
        Args:
            result: The result of an AWS action
            
        Returns:
            The formatted result as a string
        """
        # For really large results, truncate them
        try:
            if isinstance(result, dict):
                # Convert to string with indentation for readability
                return json.dumps(result, indent=2, default=str)
                
            elif isinstance(result, (list, tuple)):
                if len(result) > 20:
                    # For long lists, show just the first 10 and last 10 items
                    first_items = result[:10]
                    last_items = result[-10:]
                    
                    first_items_str = json.dumps(first_items, indent=2, default=str)
                    last_items_str = json.dumps(last_items, indent=2, default=str)
                    
                    return f"First 10 of {len(result)} items:\n{first_items_str}\n...\nLast 10 items:\n{last_items_str}"
                else:
                    # For shorter lists, show all items
                    return json.dumps(result, indent=2, default=str)
                    
            else:
                # For other types, convert to string
                return str(result)
                
        except Exception as e:
            # If we can't format the result nicely, just convert it to a string
            logger.warning(f"Error formatting result for logging: {str(e)}")
            return str(result)


class S3Helper(AWSHelper):
    """
    Helper class specifically for S3 operations.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the S3 helper.
        
        Args:
            **kwargs: Arguments to pass to the parent AWSHelper constructor
        """
        super().__init__(**kwargs)
        # Initialize S3 client and resource on creation
        self.s3_client = self.get_client('s3')
        self.s3_resource = self.get_resource('s3')
    
    def list_buckets(self) -> List[str]:
        """
        List all S3 buckets.
        
        Returns:
            A list of bucket names
        """
        with allure.step("Listing S3 buckets"):
            try:
                response = self.s3_client.list_buckets()
                buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
                
                logger.info(f"Found {len(buckets)} S3 buckets")
                allure.attach(
                    f"Buckets: {json.dumps(buckets, indent=2)}",
                    name="S3 Buckets",
                    attachment_type=allure.attachment_type.TEXT
                )
                
                return buckets
                
            except Exception as e:
                logger.exception(f"Failed to list S3 buckets: {str(e)}")
                allure.attach(
                    f"Failed to list S3 buckets: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> None:
        """
        Create an S3 bucket.
        
        Args:
            bucket_name: The name of the bucket to create
            region: The region in which to create the bucket. Defaults to the configured region.
        """
        with allure.step(f"Creating S3 bucket: {bucket_name}"):
            try:
                region = region or self.region_name
                
                # CreateBucketConfiguration is required for regions other than us-east-1
                if region == 'us-east-1':
                    response = self.s3_client.create_bucket(Bucket=bucket_name)
                else:
                    location = {'LocationConstraint': region}
                    response = self.s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration=location
                    )
                
                logger.info(f"Created S3 bucket: {bucket_name}")
                allure.attach(
                    f"Bucket: {bucket_name}\nRegion: {region}\nResponse: {json.dumps(response, default=str, indent=2)}",
                    name="S3 Bucket Created",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            except Exception as e:
                logger.exception(f"Failed to create S3 bucket {bucket_name}: {str(e)}")
                allure.attach(
                    f"Failed to create S3 bucket {bucket_name}: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> None:
        """
        Delete an S3 bucket.
        
        Args:
            bucket_name: The name of the bucket to delete
            force: Whether to force deletion by deleting all objects first
        """
        with allure.step(f"Deleting S3 bucket: {bucket_name}"):
            try:
                # If force is True, delete all objects first
                if force:
                    bucket = self.s3_resource.Bucket(bucket_name)
                    bucket.objects.all().delete()
                
                # Delete the bucket
                self.s3_client.delete_bucket(Bucket=bucket_name)
                
                logger.info(f"Deleted S3 bucket: {bucket_name}")
                allure.attach(
                    f"Bucket: {bucket_name}\nForce: {force}",
                    name="S3 Bucket Deleted",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            except Exception as e:
                logger.exception(f"Failed to delete S3 bucket {bucket_name}: {str(e)}")
                allure.attach(
                    f"Failed to delete S3 bucket {bucket_name}: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def upload_file(self, file_path: str, bucket_name: str, object_key: Optional[str] = None,
                   extra_args: Optional[Dict[str, Any]] = None) -> None:
        """
        Upload a file to an S3 bucket.
        
        Args:
            file_path: The path to the file to upload
            bucket_name: The name of the bucket to upload to
            object_key: The key to use for the uploaded object. Defaults to the file name.
            extra_args: Extra arguments to pass to the upload_file method
        """
        with allure.step(f"Uploading file to S3: {file_path} -> {bucket_name}"):
            try:
                import os
                
                # If no object key is provided, use the file name
                if object_key is None:
                    object_key = os.path.basename(file_path)
                
                # Upload the file
                self.s3_client.upload_file(
                    Filename=file_path,
                    Bucket=bucket_name,
                    Key=object_key,
                    ExtraArgs=extra_args
                )
                
                logger.info(f"Uploaded file to S3: {file_path} -> {bucket_name}/{object_key}")
                allure.attach(
                    f"File: {file_path}\nBucket: {bucket_name}\nKey: {object_key}\nExtra Args: {extra_args}",
                    name="S3 File Uploaded",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            except Exception as e:
                logger.exception(f"Failed to upload file {file_path} to S3: {str(e)}")
                allure.attach(
                    f"Failed to upload file {file_path} to S3: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def download_file(self, bucket_name: str, object_key: str, file_path: str,
                     extra_args: Optional[Dict[str, Any]] = None) -> None:
        """
        Download a file from an S3 bucket.
        
        Args:
            bucket_name: The name of the bucket to download from
            object_key: The key of the object to download
            file_path: The path where the file should be saved
            extra_args: Extra arguments to pass to the download_file method
        """
        with allure.step(f"Downloading file from S3: {bucket_name}/{object_key} -> {file_path}"):
            try:
                # Create the directory if it doesn't exist
                import os
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                # Download the file
                self.s3_client.download_file(
                    Bucket=bucket_name,
                    Key=object_key,
                    Filename=file_path,
                    ExtraArgs=extra_args
                )
                
                logger.info(f"Downloaded file from S3: {bucket_name}/{object_key} -> {file_path}")
                allure.attach(
                    f"Bucket: {bucket_name}\nKey: {object_key}\nFile: {file_path}\nExtra Args: {extra_args}",
                    name="S3 File Downloaded",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            except Exception as e:
                logger.exception(f"Failed to download file {bucket_name}/{object_key} from S3: {str(e)}")
                allure.attach(
                    f"Failed to download file {bucket_name}/{object_key} from S3: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def list_objects(self, bucket_name: str, prefix: Optional[str] = None,
                    delimiter: Optional[str] = None, max_keys: int = 1000) -> Dict[str, Any]:
        """
        List objects in an S3 bucket.
        
        Args:
            bucket_name: The name of the bucket
            prefix: Limits the response to keys that begin with the specified prefix
            delimiter: A delimiter is a character you use to group keys
            max_keys: The maximum number of keys to return
            
        Returns:
            The response from the list_objects_v2 call
        """
        with allure.step(f"Listing objects in S3 bucket: {bucket_name}"):
            try:
                # Build the request parameters
                params = {
                    'Bucket': bucket_name,
                    'MaxKeys': max_keys
                }
                
                if prefix is not None:
                    params['Prefix'] = prefix
                    
                if delimiter is not None:
                    params['Delimiter'] = delimiter
                
                # List the objects
                response = self.s3_client.list_objects_v2(**params)
                
                # Extract and log the object keys
                objects = [item['Key'] for item in response.get('Contents', [])]
                
                logger.info(f"Found {len(objects)} objects in bucket {bucket_name}")
                allure.attach(
                    f"Bucket: {bucket_name}\nPrefix: {prefix}\nDelimiter: {delimiter}\nObjects: {json.dumps(objects, indent=2)}",
                    name="S3 Objects Listed",
                    attachment_type=allure.attachment_type.TEXT
                )
                
                return response
                
            except Exception as e:
                logger.exception(f"Failed to list objects in bucket {bucket_name}: {str(e)}")
                allure.attach(
                    f"Failed to list objects in bucket {bucket_name}: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def delete_object(self, bucket_name: str, object_key: str) -> None:
        """
        Delete an object from an S3 bucket.
        
        Args:
            bucket_name: The name of the bucket
            object_key: The key of the object to delete
        """
        with allure.step(f"Deleting object from S3: {bucket_name}/{object_key}"):
            try:
                # Delete the object
                self.s3_client.delete_object(
                    Bucket=bucket_name,
                    Key=object_key
                )
                
                logger.info(f"Deleted object from S3: {bucket_name}/{object_key}")
                allure.attach(
                    f"Bucket: {bucket_name}\nKey: {object_key}",
                    name="S3 Object Deleted",
                    attachment_type=allure.attachment_type.TEXT
                )
                
            except Exception as e:
                logger.exception(f"Failed to delete object {bucket_name}/{object_key} from S3: {str(e)}")
                allure.attach(
                    f"Failed to delete object {bucket_name}/{object_key} from S3: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise
    
    def get_object_metadata(self, bucket_name: str, object_key: str) -> Dict[str, Any]:
        """
        Get the metadata of an object in an S3 bucket.
        
        Args:
            bucket_name: The name of the bucket
            object_key: The key of the object
            
        Returns:
            The object metadata
        """
        with allure.step(f"Getting metadata for S3 object: {bucket_name}/{object_key}"):
            try:
                # Get the object metadata
                response = self.s3_client.head_object(
                    Bucket=bucket_name,
                    Key=object_key
                )
                
                logger.info(f"Got metadata for S3 object: {bucket_name}/{object_key}")
                allure.attach(
                    f"Bucket: {bucket_name}\nKey: {object_key}\nMetadata: {json.dumps(response, default=str, indent=2)}",
                    name="S3 Object Metadata",
                    attachment_type=allure.attachment_type.TEXT
                )
                
                return response
                
            except Exception as e:
                logger.exception(f"Failed to get metadata for object {bucket_name}/{object_key} from S3: {str(e)}")
                allure.attach(
                    f"Failed to get metadata for object {bucket_name}/{object_key} from S3: {str(e)}",
                    name="S3 Error",
                    attachment_type=allure.attachment_type.TEXT
                )
                raise