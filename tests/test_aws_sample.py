import pytest
import allure
import os
import uuid
from utils.aws_helper import S3Helper

@pytest.mark.skip("No creds for now")
@allure.feature("AWS Testing")
@pytest.mark.aws
class TestAWSSample:
    """
    Sample AWS test class to demonstrate the usage of the AWS helpers.
    """
    
    @pytest.fixture
    def s3(self):
        """
        Fixture to provide an instance of the S3 helper.
        """
        # Initialize S3 helper with default credentials
        return S3Helper()
    
    @pytest.fixture
    def test_bucket_name(self):
        """
        Fixture to provide a unique bucket name for testing.
        """
        # Generate a unique bucket name for testing
        return f"test-bucket-{uuid.uuid4()}"
    
    @pytest.fixture
    def test_file_path(self, tmp_path):
        """
        Fixture to create a test file for S3 upload.
        """
        # Create a test file
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("This is a test file for S3 upload.")
        return str(file_path)
    
    @allure.story("S3 Operations")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description("Test S3 bucket and object operations")
    def test_s3_operations(self, s3, test_bucket_name, test_file_path):
        """Test S3 bucket and object operations."""
        
        try:
            # List buckets
            with allure.step("List S3 buckets"):
                buckets = s3.list_buckets()
                allure.attach(
                    f"Number of buckets: {len(buckets)}",
                    name="Initial Bucket Count",
                    attachment_type=allure.attachment_type.TEXT
                )
            
            # Create a bucket
            with allure.step(f"Create bucket: {test_bucket_name}"):
                s3.create_bucket(test_bucket_name)
                
                # Verify bucket was created
                new_buckets = s3.list_buckets()
                assert test_bucket_name in new_buckets, f"Bucket {test_bucket_name} was not created"
            
            # Upload a file
            with allure.step("Upload file to S3"):
                object_key = "test_object.txt"
                s3.upload_file(test_file_path, test_bucket_name, object_key)
                
                # List objects in the bucket
                response = s3.list_objects(test_bucket_name)
                objects = [item['Key'] for item in response.get('Contents', [])]
                assert object_key in objects, f"Object {object_key} was not uploaded"
            
            # Get object metadata
            with allure.step("Get object metadata"):
                metadata = s3.get_object_metadata(test_bucket_name, object_key)
                assert 'ContentLength' in metadata, "ContentLength not found in object metadata"
                assert 'ContentType' in metadata, "ContentType not found in object metadata"
            
            # Delete the object
            with allure.step("Delete object from S3"):
                s3.delete_object(test_bucket_name, object_key)
                
                # Verify object was deleted
                response = s3.list_objects(test_bucket_name)
                objects = [item['Key'] for item in response.get('Contents', [])] if 'Contents' in response else []
                assert object_key not in objects, f"Object {object_key} was not deleted"
                
        finally:
            # Clean up by deleting the bucket
            with allure.step(f"Delete bucket: {test_bucket_name}"):
                # Force deletion to ensure all objects are deleted
                s3.delete_bucket(test_bucket_name, force=True)
                
                # Verify bucket was deleted
                final_buckets = s3.list_buckets()
                assert test_bucket_name not in final_buckets, f"Bucket {test_bucket_name} was not deleted"
