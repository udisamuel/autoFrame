import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from config.config import Config
import allure


class JiraHelper:
    """Helper class for Jira integration."""
    
    def __init__(self):
        self.base_url = Config.JIRA_BASE_URL
        self.username = Config.JIRA_USERNAME
        self.api_token = Config.JIRA_API_TOKEN
        self.project_key = Config.JIRA_PROJECT_KEY
        self.issue_type = Config.JIRA_ISSUE_TYPE
        self.auth = HTTPBasicAuth(self.username, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
    def create_issue(self, 
                    summary: str, 
                    description: str, 
                    priority: str = "Medium",
                    labels: Optional[List[str]] = None,
                    components: Optional[List[str]] = None,
                    custom_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new issue in Jira.
        
        Args:
            summary: Issue summary/title
            description: Issue description
            priority: Issue priority (e.g., "High", "Medium", "Low")
            labels: List of labels to add to the issue
            components: List of components to add to the issue
            custom_fields: Dictionary of custom field IDs and values
            
        Returns:
            Dictionary containing the created issue information
        """
        url = f"{self.base_url}/rest/api/2/issue"
        
        issue_data = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": self.issue_type}
            }
        }
        
        # Only add priority if it's provided and the field is available
        if priority:
            # Some Jira instances don't allow setting priority on creation
            # We'll add it only if explicitly requested
            pass  # Will handle this after creation if needed
        
        if labels:
            issue_data["fields"]["labels"] = labels
            
        if components:
            issue_data["fields"]["components"] = [{"name": comp} for comp in components]
            
        if custom_fields:
            issue_data["fields"].update(custom_fields)
            
        try:
            response = requests.post(
                url,
                json=issue_data,
                headers=self.headers,
                auth=self.auth
            )
            response.raise_for_status()
            result = response.json()
            
            issue_key = result.get("key")
            issue_url = f"{self.base_url}/browse/{issue_key}"
            
            return {
                "key": issue_key,
                "id": result.get("id"),
                "url": issue_url,
                "self": result.get("self")
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to create Jira issue: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nResponse: {e.response.text}"
            raise Exception(error_msg)
    
    def add_attachment(self, issue_key: str, file_path: str) -> Dict[str, Any]:
        """
        Add an attachment to an existing Jira issue.
        
        Args:
            issue_key: The key of the issue (e.g., "PROJ-123")
            file_path: Path to the file to attach
            
        Returns:
            Dictionary containing attachment information
        """
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}/attachments"
        
        headers = {
            "X-Atlassian-Token": "no-check"
        }
        
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    auth=self.auth
                )
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to add attachment to Jira issue {issue_key}: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nResponse: {e.response.text}"
            raise Exception(error_msg)
    
    def create_issue_from_test_failure(self,
                                     test_name: str,
                                     error_message: str,
                                     test_code: str,
                                     screenshot_path: Optional[str] = None,
                                     ai_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a Jira issue from a test failure.
        
        Args:
            test_name: Name of the failed test
            error_message: Error message from the test failure
            test_code: Source code of the test
            screenshot_path: Path to screenshot file (if available)
            ai_analysis: AI analysis results (if available)
            
        Returns:
            Dictionary containing the created issue information
        """
        # Extract just the test name from the full path
        # e.g., "tests/test_example.py::TestClass::test_method" -> "test_method"
        if "::" in test_name:
            summary = test_name.split("::")[-1]
        else:
            summary = test_name
        
        # Build description
        description_parts = [
            f"h3. Test Failure Details",
            f"*Test Name:* {test_name}",
            f"*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"h3. Error Message",
            f"{{code}}",
            f"{error_message}",
            f"{{code}}",
            f"",
            f"h3. Test Code",
            f"{{code:python}}",
            f"{test_code}",
            f"{{code}}"
        ]
        
        # Add AI analysis if available
        if ai_analysis:
            description_parts.extend([
                f"",
                f"h3. AI Analysis",
                f"*Root Cause:* {ai_analysis.get('root_cause', 'Unknown')}",
                f"",
                f"*Suggested Fixes:*"
            ])
            for fix in ai_analysis.get('suggested_fixes', []):
                description_parts.append(f"* {fix}")
            
            if ai_analysis.get('additional_context'):
                description_parts.extend([
                    f"",
                    f"*Additional Context:*",
                    f"{ai_analysis.get('additional_context')}"
                ])
        
        description = "\n".join(description_parts)
        
        # Determine priority based on test name or AI analysis
        priority = "Medium"
        if ai_analysis and ai_analysis.get('severity'):
            severity = ai_analysis.get('severity', '').lower()
            if severity == 'critical':
                priority = "Highest"
            elif severity == 'high':
                priority = "High"
            elif severity == 'low':
                priority = "Low"
        
        # Create labels
        labels = ["test-failure", "automated-test"]
        if "api" in test_name.lower():
            labels.append("api-test")
        elif "ui" in test_name.lower() or "page" in test_name.lower():
            labels.append("ui-test")
        
        # Create the issue
        issue = self.create_issue(
            summary=summary,
            description=description,
            priority=priority,
            labels=labels
        )
        
        # Add screenshot if available
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                self.add_attachment(issue["key"], screenshot_path)
            except Exception as e:
                print(f"Warning: Failed to attach screenshot: {str(e)}")
        
        # Add Allure report link
        allure.attach(
            json.dumps(issue, indent=2),
            name="Jira Issue Created",
            attachment_type=allure.attachment_type.JSON
        )
        
        return issue
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for issues using JQL (Jira Query Language).
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            
        Returns:
            List of issues matching the query
        """
        url = f"{self.base_url}/rest/api/2/search"
        
        params = {
            "jql": jql,
            "maxResults": max_results
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                auth=self.auth
            )
            response.raise_for_status()
            return response.json().get("issues", [])
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to search Jira issues: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nResponse: {e.response.text}"
            raise Exception(error_msg)
    
    def check_duplicate_issue(self, test_name: str) -> Optional[str]:
        """
        Check if an issue already exists for a test failure.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Issue key if duplicate found, None otherwise
        """
        # Extract just the test name from the full path
        if "::" in test_name:
            simple_test_name = test_name.split("::")[-1]
        else:
            simple_test_name = test_name
            
        # Search for issues with the same test name in the summary
        jql = f'project = {self.project_key} AND summary ~ "{simple_test_name}" AND status != Done'
        
        issues = self.search_issues(jql, max_results=1)
        if issues:
            return issues[0]["key"]
        return None