"""
Jira integration helper for autoFrame.

This module provides functionality to interact with Jira, including:
- Creating issues
- Updating issues
- Searching for issues
- Linking test results to Jira issues (via Xray)
"""
import os
import json
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional, Union, Any
import logging

from config.config import Config

logger = logging.getLogger(__name__)


class JiraHelper:
    """Helper class for Jira API integration."""

    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None,
                 api_token: Optional[str] = None, project_key: Optional[str] = None):
        """Initialize the Jira helper with connection details.

        Args:
            base_url: The Jira instance URL (e.g., 'https://your-domain.atlassian.net')
            username: Jira username or email
            api_token: Jira API token
            project_key: The default Jira project key
        """
        self.base_url = base_url or Config.JIRA_BASE_URL
        self.username = username or Config.JIRA_USERNAME
        self.api_token = api_token or Config.JIRA_API_TOKEN
        self.project_key = project_key or Config.JIRA_PROJECT_KEY
        
        # Ensure the base URL doesn't end with a slash
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
            
        self.api_url = f"{self.base_url}/rest/api/3"
        self.auth = HTTPBasicAuth(self.username, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def create_issue(self, summary: str, description: str, issue_type: str = "Bug",
                     priority: str = "Medium", labels: List[str] = None,
                     components: List[str] = None, custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new Jira issue.

        Args:
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (Bug, Task, Story, etc.)
            priority: Priority level
            labels: List of labels to add
            components: List of component names
            custom_fields: Dictionary of custom field IDs and values

        Returns:
            Response data containing the created issue details
        """
        labels = labels or []
        components = components or []
        custom_fields = custom_fields or {}
        
        # Convert components list to the format Jira expects
        component_data = [{"name": comp} for comp in components]
        
        # Basic issue data
        issue_data = {
            "fields": {
                "project": {
                    "key": self.project_key
                },
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "name": issue_type
                },
                "priority": {
                    "name": priority
                },
                "labels": labels,
                "components": component_data
            }
        }
        
        # Add any custom fields
        for field_id, value in custom_fields.items():
            issue_data["fields"][field_id] = value
            
        # Create the issue
        url = f"{self.api_url}/issue"
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=issue_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Jira issue: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def update_issue(self, issue_key: str, fields_to_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Jira issue.

        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            fields_to_update: Dictionary of fields to update

        Returns:
            Response data
        """
        url = f"{self.api_url}/issue/{issue_key}"
        
        # Format the update data
        update_data = {
            "fields": fields_to_update
        }
        
        try:
            response = requests.put(
                url,
                auth=self.auth,
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            return {"success": True, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update Jira issue {issue_key}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add a comment to a Jira issue.

        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            comment: The comment text

        Returns:
            Response data containing the created comment details
        """
        url = f"{self.api_url}/issue/{issue_key}/comment"
        
        comment_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=comment_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add comment to Jira issue {issue_key}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Get details of a specific Jira issue.

        Args:
            issue_key: The issue key (e.g., PROJECT-123)

        Returns:
            Response data containing the issue details
        """
        url = f"{self.api_url}/issue/{issue_key}"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Jira issue {issue_key}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def search_issues(self, jql: str, max_results: int = 50, fields: List[str] = None) -> Dict[str, Any]:
        """Search for Jira issues using JQL.

        Args:
            jql: JQL search query
            max_results: Maximum number of results to return
            fields: List of fields to include in the response

        Returns:
            Response data containing the search results
        """
        url = f"{self.api_url}/search"
        
        fields = fields or ["summary", "status", "assignee", "description"]
        
        query_params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields)
        }
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                params=query_params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search Jira issues with JQL '{jql}': {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def create_issue_link(self, link_type: str, inward_issue: str, outward_issue: str, comment: str = None) -> Dict[str, Any]:
        """Create a link between two Jira issues.

        Args:
            link_type: The name of the link type (e.g., "Relates to")
            inward_issue: The issue key for the inward issue
            outward_issue: The issue key for the outward issue
            comment: Optional comment to add with the link

        Returns:
            Response data
        """
        url = f"{self.api_url}/issueLink"
        
        link_data = {
            "type": {
                "name": link_type
            },
            "inwardIssue": {
                "key": inward_issue
            },
            "outwardIssue": {
                "key": outward_issue
            }
        }
        
        if comment:
            link_data["comment"] = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=link_data
            )
            response.raise_for_status()
            return {"success": True, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create issue link between {inward_issue} and {outward_issue}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        """Transition a Jira issue to a different state.

        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            transition_id: The ID of the transition

        Returns:
            Response data
        """
        url = f"{self.api_url}/issue/{issue_key}/transitions"
        
        transition_data = {
            "transition": {
                "id": transition_id
            }
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=self.headers,
                json=transition_data
            )
            response.raise_for_status()
            return {"success": True, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to transition Jira issue {issue_key}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_available_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available transitions for a Jira issue.

        Args:
            issue_key: The issue key (e.g., PROJECT-123)

        Returns:
            Response data containing available transitions
        """
        url = f"{self.api_url}/issue/{issue_key}/transitions"
        
        try:
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get transitions for Jira issue {issue_key}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def upload_attachment(self, issue_key: str, file_path: str) -> Dict[str, Any]:
        """Upload an attachment to a Jira issue.

        Args:
            issue_key: The issue key (e.g., PROJECT-123)
            file_path: Path to the file to upload

        Returns:
            Response data containing the attachment details
        """
        url = f"{self.api_url}/issue/{issue_key}/attachments"
        
        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }
        
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            
            try:
                response = requests.post(
                    url,
                    auth=self.auth,
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to upload attachment to Jira issue {issue_key}: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                raise
