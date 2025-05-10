import openai
from typing import Dict, Any, List, Optional, Union
import json
import os
import logging
import re
from config.config import Config

logger = logging.getLogger(__name__)

class AITestAnalyzer:
    """Helper class for analyzing test results using AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key, otherwise use from config."""
        self.api_key = api_key or Config.OPENAI_API_KEY
        openai.api_key = self.api_key
    
    def analyze_test_failure(self,
                           test_name: str,
                           error_message: str,
                           test_code: str,
                           screenshot_path: Optional[str] = None,
                           response_data: Optional[Union[Dict[str, Any], str]] = None) -> Dict[str, Any]:
        """
        Analyze a test failure and provide insights on potential root causes.
        
        Args:
            test_name: Name of the failed test
            error_message: Error message from the test failure
            test_code: Source code of the test function
            screenshot_path: Optional path to a screenshot (for UI tests)
            response_data: Optional API response data (for API tests)
            
        Returns:
            Dictionary with analysis results including potential causes and suggestions
        """
        # Prepare the input data
        input_data = {
            "test_name": test_name,
            "error_message": error_message,
            "test_code": test_code
        }
        
        if response_data:
            if isinstance(response_data, dict):
                input_data["response_data"] = json.dumps(response_data)
            else:
                input_data["response_data"] = response_data
                
        # Create a prompt for the AI
        prompt = f"""
        Analyze this test failure and provide insights:
        
        Test Name: {input_data['test_name']}
        
        Error Message:
        {input_data['error_message']}
        
        Test Code:
        ```python
        {input_data['test_code']}
        ```
        """
        
        if "response_data" in input_data:
            prompt += f"""
            Response Data:
            ```
            {input_data['response_data']}
            ```
            """
        
        if screenshot_path and os.path.exists(screenshot_path):
            prompt += f"\nNote: A screenshot was captured at the time of failure."
        
        prompt += """
        Please provide:
        1. Likely root cause of the failure
        2. Suggested fixes
        3. Prevention strategies
        
        Output in JSON format with these fields.
        """
        
        try:
            # Call the AI to analyze the failure
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test automation expert that analyzes test failures."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # If no JSON formatting, try to parse the whole content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Extract insights using regex if JSON parsing fails
                root_cause_match = re.search(r'(?:root cause|Root cause):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                root_cause = root_cause_match.group(1).strip() if root_cause_match else "Unable to determine the root cause"
                
                fixes_match = re.search(r'(?:Suggested fixes|suggested fixes):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                fixes_text = fixes_match.group(1).strip() if fixes_match else "No specific fixes suggested"
                fixes = [fix.strip() for fix in fixes_text.split('\n') if fix.strip()]
                
                prevention_match = re.search(r'(?:Prevention strategies|prevention strategies):\s*(.*?)(?:\n\n|\Z)', content, re.DOTALL)
                prevention_text = prevention_match.group(1).strip() if prevention_match else "No prevention strategies suggested"
                prevention = [strategy.strip() for strategy in prevention_text.split('\n') if strategy.strip()]
                
                return {
                    "root_cause": root_cause,
                    "suggested_fixes": fixes,
                    "prevention_strategies": prevention
                }
        except Exception as e:
            logger.error(f"Error analyzing test failure: {e}")
            # Fallback to a simple structure if parsing fails
            return {
                "root_cause": "Unable to determine the root cause automatically.",
                "suggested_fixes": ["Review the error message and test code manually."],
                "prevention_strategies": ["Increase test logging for more context."]
            }
    
    def analyze_test_patterns(self, recent_test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns in recent test results.
        
        Args:
            recent_test_results: List of recent test results with status, duration, etc.
            
        Returns:
            Dictionary with pattern analysis
        """
        if not recent_test_results or len(recent_test_results) < 5:
            return {"status": "insufficient_data", "message": "Need at least 5 test results for pattern analysis"}
        
        # Format the test results data
        results_summary = []
        for i, result in enumerate(recent_test_results[-20:]):  # Only use the 20 most recent results
            results_summary.append({
                "test_name": result.get("test_name", f"test_{i}"),
                "status": result.get("status", "unknown"),
                "duration": result.get("duration", 0),
                "timestamp": result.get("timestamp", "unknown"),
                "error": result.get("error", "") if result.get("status") != "passed" else ""
            })
        
        prompt = f"""
        Analyze these recent test results and identify any patterns or trends:
        
        {json.dumps(results_summary, indent=2)}
        
        Please identify:
        1. Flaky tests (tests that alternate between pass and fail)
        2. Consistently failing tests
        3. Tests with increasing duration
        4. Any correlations between failures
        5. Any other notable patterns
        
        Output in JSON format with these fields.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test analytics expert that identifies patterns in test results."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Extract the response
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # If no JSON formatting, try to parse the whole content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Structured fallback
                return {
                    "status": "analysis_completed",
                    "message": content,
                    "flaky_tests": [],
                    "failing_tests": [],
                    "slow_tests": [],
                    "correlations": [],
                    "other_patterns": []
                }
        except Exception as e:
            logger.error(f"Error analyzing test patterns: {e}")
            return {
                "status": "analysis_failed",
                "message": f"Failed to analyze test patterns: {str(e)}",
                "flaky_tests": [],
                "failing_tests": [],
                "slow_tests": [],
                "correlations": [],
                "other_patterns": []
            }
    
    def suggest_test_improvements(self, test_code: str) -> Dict[str, Any]:
        """
        Suggest improvements for a test case.
        
        Args:
            test_code: Source code of the test function
            
        Returns:
            Dictionary with suggested improvements
        """
        prompt = f"""
        Review this test code and suggest improvements:
        
        ```python
        {test_code}
        ```
        
        Please suggest improvements for:
        1. Readability
        2. Maintainability
        3. Robustness
        4. Best practices
        5. Performance
        
        Output in JSON format with these fields.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a test automation expert that suggests test improvements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Extract the response
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # If no JSON formatting, try to parse the whole content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Extract suggestions using regex if JSON parsing fails
                readability_match = re.search(r'(?:Readability|readability):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                readability = readability_match.group(1).strip() if readability_match else "No suggestions for readability"
                
                maintainability_match = re.search(r'(?:Maintainability|maintainability):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                maintainability = maintainability_match.group(1).strip() if maintainability_match else "No suggestions for maintainability"
                
                robustness_match = re.search(r'(?:Robustness|robustness):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                robustness = robustness_match.group(1).strip() if robustness_match else "No suggestions for robustness"
                
                best_practices_match = re.search(r'(?:Best practices|best practices):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                best_practices = best_practices_match.group(1).strip() if best_practices_match else "No suggestions for best practices"
                
                performance_match = re.search(r'(?:Performance|performance):\s*(.*?)(?:\n\n|\Z)', content, re.DOTALL)
                performance = performance_match.group(1).strip() if performance_match else "No suggestions for performance"
                
                return {
                    "readability": readability,
                    "maintainability": maintainability,
                    "robustness": robustness,
                    "best_practices": best_practices,
                    "performance": performance
                }
        except Exception as e:
            logger.error(f"Error suggesting test improvements: {e}")
            return {
                "status": "analysis_failed",
                "message": f"Failed to analyze test: {str(e)}",
                "suggestions": ["Review the test manually for potential improvements."]
            }
