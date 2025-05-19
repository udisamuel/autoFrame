"""
Xray integration helper for autoFrame.

This module provides functionality to integrate with Xray for Jira, including:
- Retrieving test information from Xray
- Reporting test results back to Xray
- Creating test execution issues
- Supporting both Xray Cloud and Xray Server/Data Center
"""
import os
import json
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime

from config.config import Config
from utils.jira_helper import JiraHelper

logger = logging.getLogger(__name__)


class XrayHelper:
    """Helper class for Xray API integration."""

    def __init__(self, jira_helper: Optional[JiraHelper] = None, 
                 xray_cloud: Optional[bool] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        """Initialize the Xray helper with connection details.

        Args:
            jira_helper: JiraHelper instance for Jira API calls
            xray_cloud: Whether using Xray Cloud (True) or Server/DC (False)
            client_id: Xray Cloud client ID (only for Xray Cloud)
            client_secret: Xray Cloud client secret (only for Xray Cloud)
        """
        self.jira_helper = jira_helper or JiraHelper()
        self.is_cloud = xray_cloud if xray_cloud is not None else Config.XRAY_CLOUD
        self.client_id = client_id or Config.XRAY_CLIENT_ID
        self.client_secret = client_secret or Config.XRAY_CLIENT_SECRET
        
        # Set up API URLs based on whether we're using Xray Cloud or Server/DC
        if self.is_cloud:
            self.api_base_url = "https://xray.cloud.getxray.app/api/v2"
            self.auth_url = "https://xray.cloud.getxray.app/api/v2/authenticate"
        else:
            # For Server/DC, we use the Jira API URL with Xray endpoints
            self.api_base_url = f"{self.jira_helper.base_url}/rest/raven/1.0"
            
        # For Xray Cloud, initialize the auth token
        self.cloud_auth_token = None
        if self.is_cloud:
            self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Xray Cloud and get an auth token."""
        if not self.is_cloud:
            return  # Not needed for Server/DC
            
        auth_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(
                self.auth_url,
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            self.cloud_auth_token = response.text.strip('"')  # Response is a quoted token
            
            # Set up headers with the token
            self.headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.cloud_auth_token}"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to authenticate with Xray Cloud: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def create_test_execution(self, summary: str, description: str, test_keys: List[str],
                              assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Test Execution issue in Jira.

        Args:
            summary: Test execution summary
            description: Test execution description
            test_keys: List of Xray test issue keys to include
            assignee: Optional assignee for the execution

        Returns:
            Response data containing the created Test Execution details
        """
        if self.is_cloud:
            return self._create_test_execution_cloud(summary, description, test_keys, assignee)
        else:
            return self._create_test_execution_server(summary, description, test_keys, assignee)
    
    def _create_test_execution_cloud(self, summary: str, description: str, test_keys: List[str],
                                    assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a test execution for Xray Cloud."""
        url = f"{self.api_base_url}/import/execution"
        
        execution_data = {
            "fields": {
                "project": {
                    "key": self.jira_helper.project_key
                },
                "summary": summary,
                "description": description,
                "issuetype": {
                    "name": "Test Execution"
                }
            },
            "tests": test_keys
        }
        
        if assignee:
            execution_data["fields"]["assignee"] = {"name": assignee}
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=execution_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create test execution in Xray Cloud: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def _create_test_execution_server(self, summary: str, description: str, test_keys: List[str],
                                     assignee: Optional[str] = None) -> Dict[str, Any]:
        """Create a test execution for Xray Server/DC."""
        # For Server/DC, first create the Test Execution issue
        custom_fields = {
            Config.XRAY_TEST_EXECUTION_TYPE_FIELD: {"value": "automation"}
        }
        
        execution = self.jira_helper.create_issue(
            summary=summary,
            description=description,
            issue_type="Test Execution",
            custom_fields=custom_fields
        )
        
        execution_key = execution["key"]
        
        # Now add tests to the execution
        test_data = {
            "add": test_keys
        }
        
        url = f"{self.api_base_url}/api/testexec/{execution_key}/test"
        
        try:
            response = requests.post(
                url,
                auth=self.jira_helper.auth,
                headers=self.jira_helper.headers,
                json=test_data
            )
            response.raise_for_status()
            return {"key": execution_key, "tests_added": test_keys}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add tests to execution {execution_key}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def report_test_results(self, execution_key: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Report test results to an existing Test Execution.

        Args:
            execution_key: Test Execution issue key
            results: List of test results in the format:
                     [
                         {
                             "test_key": "TEST-123",
                             "status": "PASS/FAIL/TODO/EXECUTING",
                             "comment": "Optional comment",
                             "evidence": ["path/to/file1.png", "path/to/file2.log"],
                             "duration": 1532,  # Time in milliseconds
                             "start_date": "2023-10-20T10:00:00Z",  # ISO format
                             "finish_date": "2023-10-20T10:00:15Z"  # ISO format
                         },
                         ...
                     ]

        Returns:
            Response data
        """
        if self.is_cloud:
            return self._report_test_results_cloud(execution_key, results)
        else:
            return self._report_test_results_server(execution_key, results)
    
    def _report_test_results_cloud(self, execution_key: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Report test results for Xray Cloud."""
        url = f"{self.api_base_url}/import/execution/results"
        
        formatted_results = []
        for result in results:
            test_result = {
                "testKey": result["test_key"],
                "status": result["status"],
                "comment": result.get("comment", "")
            }
            
            # Add optional fields if provided
            if "duration" in result:
                test_result["duration"] = result["duration"]
                
            if "start_date" in result:
                test_result["startedOn"] = result["start_date"]
                
            if "finish_date" in result:
                test_result["finishedOn"] = result["finish_date"]
            
            # Add evidence files if provided
            if result.get("evidence"):
                evidence_list = []
                for evidence_path in result["evidence"]:
                    file_name = os.path.basename(evidence_path)
                    with open(evidence_path, "rb") as file:
                        file_content = file.read()
                        evidence_list.append({
                            "filename": file_name,
                            "contentType": self._get_content_type(file_name),
                            "data": file_content.encode("base64")
                        })
                test_result["evidences"] = evidence_list
                
            formatted_results.append(test_result)
        
        execution_data = {
            "testExecutionKey": execution_key,
            "tests": formatted_results
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=execution_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report test results to Xray Cloud: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def _report_test_results_server(self, execution_key: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Report test results for Xray Server/DC."""
        url = f"{self.api_base_url}/api/testexec/{execution_key}/results"
        
        formatted_results = []
        for result in results:
            test_result = {
                "testKey": result["test_key"],
                "status": result["status"]
            }
            
            # Add optional fields if provided
            if "comment" in result:
                test_result["comment"] = result["comment"]
                
            if "duration" in result:
                test_result["executedTime"] = result["duration"]
                
            if "start_date" in result and "finish_date" in result:
                test_result["started"] = result["start_date"]
                test_result["finished"] = result["finish_date"]
                
            formatted_results.append(test_result)
        
        # For Server, upload evidence files separately after reporting results
        try:
            response = requests.post(
                url,
                auth=self.jira_helper.auth,
                headers=self.jira_helper.headers,
                json=formatted_results
            )
            response.raise_for_status()
            
            # Upload evidence files if provided
            for result in results:
                if result.get("evidence"):
                    for evidence_path in result["evidence"]:
                        self._upload_test_evidence_server(
                            execution_key, 
                            result["test_key"], 
                            evidence_path
                        )
            
            return {"success": True, "execution_key": execution_key, "tests_reported": len(results)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report test results to Xray Server: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def _upload_test_evidence_server(self, execution_key: str, test_key: str, file_path: str) -> Dict[str, Any]:
        """Upload test evidence for Xray Server/DC."""
        url = f"{self.api_base_url}/api/testexec/{execution_key}/test/{test_key}/attachment"
        
        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }
        
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            
            try:
                response = requests.post(
                    url,
                    auth=self.jira_helper.auth,
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                return {"success": True, "status_code": response.status_code}
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to upload test evidence: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                raise

    def import_results_from_junit(self, execution_key: str, junit_path: str, 
                                 test_plan_key: Optional[str] = None) -> Dict[str, Any]:
        """Import JUnit XML test results into Xray.

        Args:
            execution_key: Test Execution issue key, or None to create a new execution
            junit_path: Path to the JUnit XML file
            test_plan_key: Optional Test Plan issue key to link the execution to

        Returns:
            Response data
        """
        if self.is_cloud:
            return self._import_results_from_junit_cloud(execution_key, junit_path, test_plan_key)
        else:
            return self._import_results_from_junit_server(execution_key, junit_path, test_plan_key)
    
    def _import_results_from_junit_cloud(self, execution_key: str, junit_path: str,
                                        test_plan_key: Optional[str] = None) -> Dict[str, Any]:
        """Import JUnit results for Xray Cloud."""
        if execution_key:
            url = f"{self.api_base_url}/import/execution/junit/results"
        else:
            url = f"{self.api_base_url}/import/execution/junit"
            
        with open(junit_path, 'r') as file:
            junit_content = file.read()
            
        info = {
            "fields": {
                "project": {
                    "key": self.jira_helper.project_key
                },
                "summary": f"Automated Test Execution - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "description": "Test results imported from JUnit XML report"
            }
        }
        
        if execution_key:
            info["testExecutionKey"] = execution_key
            
        if test_plan_key:
            info["testPlanKey"] = test_plan_key
            
        multipart_data = {
            "info": json.dumps(info),
            "file": junit_content
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                files=multipart_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to import JUnit results to Xray Cloud: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def _import_results_from_junit_server(self, execution_key: str, junit_path: str,
                                         test_plan_key: Optional[str] = None) -> Dict[str, Any]:
        """Import JUnit results for Xray Server/DC."""
        url_endpoint = "importExecutionResults" if execution_key else "import/execution/junit"
        url = f"{self.api_base_url}/api/{url_endpoint}"
        
        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }
        
        params = {}
        if execution_key:
            params["testExecKey"] = execution_key
        else:
            params["projectKey"] = self.jira_helper.project_key
            
        if test_plan_key:
            params["testPlanKey"] = test_plan_key
        
        with open(junit_path, 'rb') as file:
            files = {'file': (os.path.basename(junit_path), file)}
            
            try:
                response = requests.post(
                    url,
                    auth=self.jira_helper.auth,
                    headers=headers,
                    params=params,
                    files=files
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to import JUnit results to Xray Server: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                raise

    def get_test_by_id(self, test_key: str) -> Dict[str, Any]:
        """Get test details from Xray.

        Args:
            test_key: The Test issue key

        Returns:
            Response data containing test details
        """
        if self.is_cloud:
            url = f"{self.api_base_url}/api/tests/{test_key}"
            headers = self.headers
            auth = None
        else:
            url = f"{self.api_base_url}/api/test/{test_key}"
            headers = self.jira_helper.headers
            auth = self.jira_helper.auth
            
        try:
            response = requests.get(
                url,
                auth=auth,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get test {test_key} from Xray: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_tests_by_execution(self, execution_key: str) -> List[Dict[str, Any]]:
        """Get all tests in a test execution.

        Args:
            execution_key: The Test Execution issue key

        Returns:
            List of test details
        """
        if self.is_cloud:
            url = f"{self.api_base_url}/api/testexecutions/{execution_key}/tests"
            headers = self.headers
            auth = None
        else:
            url = f"{self.api_base_url}/api/testexec/{execution_key}/test"
            headers = self.jira_helper.headers
            auth = self.jira_helper.auth
            
        try:
            response = requests.get(
                url,
                auth=auth,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get tests for execution {execution_key} from Xray: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def _get_content_type(self, filename: str) -> str:
        """Get the content type based on file extension."""
        extension = os.path.splitext(filename)[1].lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.log': 'text/plain',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.json': 'application/json',
            '.xml': 'application/xml'
        }
        return content_types.get(extension, 'application/octet-stream')
