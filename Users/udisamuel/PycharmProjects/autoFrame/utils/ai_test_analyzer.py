import logging
from typing import Dict, Any, List, Optional, Union
import json
import os
import re
from config.config import Config

logger = logging.getLogger(__name__)

# Check if OpenAI is available
OPENAI_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not found. AI test analysis will use basic analysis.")

class AITestAnalyzer:
    """Helper class for analyzing test results using AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key, otherwise use from config."""
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.openai_available = OPENAI_AVAILABLE
        
        if self.openai_available:
            try:
                openai.api_key = self.api_key
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_available = False
    
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
        if self.openai_available and self.api_key:
            try:
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
                        
                # Create prompt for the AI
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
                
                # Call the AI
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
                logger.error(f"Error analyzing test failure with AI: {e}")
                # Fall through to the fallback method
        
        # Fallback method: perform basic analysis
        return self._analyze_test_failure_fallback(test_name, error_message, test_code, screenshot_path, response_data)
    
    def _analyze_test_failure_fallback(self, 
                                      test_name: str,
                                      error_message: str,
                                      test_code: str,
                                      screenshot_path: Optional[str] = None,
                                      response_data: Optional[Union[Dict[str, Any], str]] = None) -> Dict[str, Any]:
        """Perform basic test failure analysis when AI is not available."""
        analysis = {
            "root_cause": "Analysis performed without AI - check error message for details",
            "suggested_fixes": [],
            "prevention_strategies": [
                "Add more detailed logging",
                "Review test assertions",
                "Consider adding more specific error handling"
            ]
        }
        
        # Common assertion failures
        if "AssertionError" in error_message:
            analysis["root_cause"] = "Assertion failure - test expectation was not met"
            analysis["suggested_fixes"].append("Review the assertion that failed and check if the expectation is correct")
            analysis["suggested_fixes"].append("Verify the application behavior to confirm if it's a test issue or application issue")
        
        # Locator/element failures in UI tests
        elif any(term in error_message for term in ["no such element", "element not found", "selector", "locator"]):
            analysis["root_cause"] = "Element not found or selector issue in UI test"
            analysis["suggested_fixes"].append("Check if the element selector is correct")
            analysis["suggested_fixes"].append("Verify if the element is present in the page")
            analysis["suggested_fixes"].append("Add explicit waits before interacting with the element")
        
        # Connection/timeout errors
        elif any(term in error_message for term in ["timeout", "connection", "refused", "unavailable"]):
            analysis["root_cause"] = "Connection or timeout error"
            analysis["suggested_fixes"].append("Check if the service/endpoint is available")
            analysis["suggested_fixes"].append("Increase timeout values")
            analysis["suggested_fixes"].append("Verify network connectivity")
        
        # Authentication/permission errors
        elif any(term in error_message for term in ["unauthorized", "forbidden", "permission", "auth"]):
            analysis["root_cause"] = "Authentication or permission issue"
            analysis["suggested_fixes"].append("Check authentication credentials")
            analysis["suggested_fixes"].append("Verify permission settings")
        
        # Data validation errors
        elif any(term in error_message for term in ["schema", "validation", "invalid", "format"]):
            analysis["root_cause"] = "Data validation or format issue"
            analysis["suggested_fixes"].append("Check data format and schema requirements")
            analysis["suggested_fixes"].append("Verify if test data matches expected format")
        
        # Specific response issues if response data is available
        if response_data:
            if isinstance(response_data, dict) and response_data.get("error"):
                analysis["root_cause"] = f"API response contained an error: {response_data.get('error')}"
                analysis["suggested_fixes"].append("Handle the specific API error in the test")
        
        # Screenshot available
        if screenshot_path and os.path.exists(screenshot_path):
            analysis["suggested_fixes"].append("Review the failure screenshot for visual clues")
        
        return analysis
    
    def analyze_test_patterns(self, recent_test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze patterns in recent test results.
        
        Args:
            recent_test_results: List of recent test results with status, duration, etc.
            
        Returns:
            Dictionary with pattern analysis
        """
        if self.openai_available and self.api_key and len(recent_test_results) >= 5:
            try:
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
                logger.error(f"Error analyzing test patterns with AI: {e}")
                # Fall through to the fallback method
        
        # Fallback: perform basic pattern analysis
        return self._analyze_test_patterns_fallback(recent_test_results)
    
    def _analyze_test_patterns_fallback(self, recent_test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform basic test pattern analysis when AI is not available."""
        if len(recent_test_results) < 5:
            return {
                "status": "insufficient_data",
                "message": "Need at least 5 test results for pattern analysis",
                "flaky_tests": [],
                "failing_tests": [],
                "slow_tests": [],
                "correlations": [],
                "other_patterns": []
            }
        
        # Process test results
        test_status_map = {}
        test_duration_map = {}
        
        for result in recent_test_results:
            test_name = result.get("test_name", "unknown")
            status = result.get("status", "unknown")
            duration = result.get("duration", 0)
            
            # Track status history
            if test_name not in test_status_map:
                test_status_map[test_name] = []
            test_status_map[test_name].append(status)
            
            # Track duration history
            if test_name not in test_duration_map:
                test_duration_map[test_name] = []
            test_duration_map[test_name].append(duration)
        
        # Identify flaky tests (alternating pass/fail)
        flaky_tests = []
        for test_name, statuses in test_status_map.items():
            if len(statuses) >= 3:  # Need at least 3 runs to determine flakiness
                pass_count = statuses.count("passed")
                fail_count = len(statuses) - pass_count
                
                # Consider it flaky if it has both passes and failures
                if pass_count > 0 and fail_count > 0:
                    flaky_tests.append({
                        "test_name": test_name,
                        "pass_rate": pass_count / len(statuses)
                    })
        
        # Identify consistently failing tests
        failing_tests = []
        for test_name, statuses in test_status_map.items():
            if len(statuses) >= 2:  # Need at least 2 runs
                # Consider it consistently failing if it failed in all recent runs
                if all(status != "passed" for status in statuses):
                    failing_tests.append(test_name)
        
        # Identify tests with increasing duration
        slow_tests = []
        for test_name, durations in test_duration_map.items():
            if len(durations) >= 3:  # Need at least 3 runs to detect a trend
                # Check if durations are generally increasing
                is_increasing = all(durations[i] <= durations[i+1] for i in range(len(durations)-1))
                
                if is_increasing and (durations[-1] > durations[0] * 1.1):  # 10% increase from first to last
                    slow_tests.append({
                        "test_name": test_name,
                        "first_duration": durations[0],
                        "last_duration": durations[-1],
                        "percent_increase": ((durations[-1] - durations[0]) / durations[0]) * 100
                    })
        
        return {
            "status": "analysis_completed",
            "message": "Basic test pattern analysis completed",
            "flaky_tests": flaky_tests,
            "failing_tests": failing_tests,
            "slow_tests": slow_tests,
            "correlations": [],  # Basic analysis can't detect correlations easily
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
        if self.openai_available and self.api_key:
            try:
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
                logger.error(f"Error suggesting test improvements with AI: {e}")
                # Fall through to the fallback method
        
        # Fallback: provide basic improvement suggestions
        return self._suggest_test_improvements_fallback(test_code)
    
    def _suggest_test_improvements_fallback(self, test_code: str) -> Dict[str, Any]:
        """Provide basic test improvement suggestions when AI is not available."""
        # Check for common improvement areas
        has_docstring = '"""' in test_code or "'''" in test_code
        has_setup_comments = "# Setup" in test_code
        has_execute_comments = "# Execute" in test_code or "# Action" in test_code
        has_assert_comments = "# Assert" in test_code or "# Verify" in test_code
        has_allure_annotations = "@allure" in test_code
        
        suggestions = {
            "readability": [],
            "maintainability": [],
            "robustness": [],
            "best_practices": [],
            "performance": []
        }
        
        # Readability suggestions
        if not has_docstring:
            suggestions["readability"].append("Add a docstring to describe the test purpose and expectations")
        
        if not (has_setup_comments and has_execute_comments and has_assert_comments):
            suggestions["readability"].append("Use section comments (# Setup, # Execute, # Assert) to clarify test structure")
        
        # Maintainability suggestions
        suggestions["maintainability"].append("Use descriptive variable names to make the test intent clear")
        suggestions["maintainability"].append("Extract reusable test steps into helper methods")
        
        # Robustness suggestions
        suggestions["robustness"].append("Add proper error handling and recovery for test actions")
        suggestions["robustness"].append("Use explicit waits instead of fixed sleeps for UI tests")
        suggestions["robustness"].append("Include validation checks before critical actions")
        
        # Best practices suggestions
        if not has_allure_annotations:
            suggestions["best_practices"].append("Add Allure annotations for better test reporting")
        
        suggestions["best_practices"].append("Ensure test follows AAA pattern (Arrange, Act, Assert)")
        suggestions["best_practices"].append("Make tests independent of each other")
        
        # Performance suggestions
        suggestions["performance"].append("Minimize external calls and database interactions in tests")
        suggestions["performance"].append("Use parameterization for similar test cases")
        
        # Format suggestions as strings
        for category in suggestions:
            if suggestions[category]:
                suggestions[category] = "\n".join(f"- {suggestion}" for suggestion in suggestions[category])
            else:
                suggestions[category] = "No specific suggestions."
        
        return suggestions
