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
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = Config.OPENAI_MODEL or "gpt-3.5-turbo"
    
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
        
        Format your response as a JSON object with these specific keys:
        - root_cause
        - suggested_fixes (as an array)
        - prevention_strategies (as an array)
        """
        
        try:
            # Call the AI to analyze the failure using the new OpenAI API format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test automation expert that analyzes test failures. Always output analysis in a structured JSON format with all the requested fields."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Parse the response - new API format returns different structure
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
                try:
                    result = json.loads(json_str)
                    # Ensure all expected fields are present
                    if not all(key in result for key in ["root_cause", "suggested_fixes", "prevention_strategies"]):
                        logger.warning("AI response missing some expected fields")
                        # Add any missing fields
                        if "root_cause" not in result:
                            result["root_cause"] = "Unable to determine the root cause automatically."
                        if "suggested_fixes" not in result:
                            result["suggested_fixes"] = ["Review the error message and test code manually."]
                        if "prevention_strategies" not in result:
                            result["prevention_strategies"] = ["Increase test logging for more context."]
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {e}")
            
            # If JSON extraction fails, try to parse the whole content
            try:
                result = json.loads(content)
                # Ensure all expected fields are present
                if "root_cause" not in result:
                    result["root_cause"] = "Unable to determine the root cause automatically."
                if "suggested_fixes" not in result:
                    result["suggested_fixes"] = ["Review the error message and test code manually."]
                if "prevention_strategies" not in result:
                    result["prevention_strategies"] = ["Increase test logging for more context."]
                return result
            except json.JSONDecodeError:
                # Extract insights using regex if JSON parsing fails
                logger.info("Using regex to extract insights from non-JSON response")
                
                root_cause_match = re.search(r'(?:root cause|Root cause):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                root_cause = root_cause_match.group(1).strip() if root_cause_match else "Unable to determine the root cause"
                
                fixes_match = re.search(r'(?:Suggested fixes|suggested fixes):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                fixes_text = fixes_match.group(1).strip() if fixes_match else "No specific fixes suggested"
                fixes = [fix.strip() for fix in fixes_text.split('\n') if fix.strip()]
                
                prevention_match = re.search(r'(?:Prevention strategies|prevention strategies):\s*(.*?)(?:\n\n|\Z)', content, re.DOTALL)
                prevention_text = prevention_match.group(1).strip() if prevention_match else "No prevention strategies suggested"
                prevention = [strategy.strip() for strategy in prevention_text.split('\n') if strategy.strip()]
                
                # If no fixes or prevention strategies were found, use the defaults
                if not fixes:
                    fixes = ["Review the error message and test code manually."]
                if not prevention:
                    prevention = ["Increase test logging for more context."]
                
                # If none of the regex matches worked, use the whole content for root cause
                if not any([root_cause_match, fixes_match, prevention_match]):
                    logger.warning("Could not extract structured insights, using raw content")
                    return {
                        "root_cause": "AI output was not in expected format. Raw response: " + content[:200] + "...",
                        "suggested_fixes": ["Review the error message and test code manually."],
                        "prevention_strategies": ["Increase test logging for more context."]
                    }
                
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
            return {
                "status": "insufficient_data", 
                "message": "Need at least 5 test results for pattern analysis",
                "flaky_tests": [],
                "failing_tests": [],
                "slow_tests": [],
                "correlations": [],
                "other_patterns": []
            }
        
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
        
        Format your response as a JSON object with these specific keys:
        - flaky_tests (as an array)
        - failing_tests (as an array)
        - slow_tests (as an array)
        - correlations (as an array)
        - other_patterns (as an array)
        - status (with value "analysis_completed")
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test analytics expert that identifies patterns in test results. Always output analysis in a structured JSON format with all the requested fields."},
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
                try:
                    result = json.loads(json_str)
                    # Ensure all expected fields are present
                    expected_fields = ["flaky_tests", "failing_tests", "slow_tests", 
                                     "correlations", "other_patterns", "status"]
                    for field in expected_fields:
                        if field not in result:
                            if field == "status":
                                result[field] = "analysis_completed"
                            else:
                                result[field] = []
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {e}")
            
            # If JSON extraction fails, try to parse the whole content
            try:
                result = json.loads(content)
                # Ensure all expected fields are present
                expected_fields = ["flaky_tests", "failing_tests", "slow_tests", 
                                 "correlations", "other_patterns", "status"]
                for field in expected_fields:
                    if field not in result:
                        if field == "status":
                            result[field] = "analysis_completed"
                        else:
                            result[field] = []
                return result
            except json.JSONDecodeError:
                # Structured fallback if no JSON could be extracted
                logger.warning("Could not extract structured patterns, using fallback")
                
                # Identify patterns manually from the text content
                flaky_tests = []
                failing_tests = []
                slow_tests = []
                correlations = []
                other_patterns = []
                
                # Try to extract pattern information using regex
                flaky_match = re.search(r'(?:Flaky tests|flaky tests):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                if flaky_match:
                    flaky_text = flaky_match.group(1).strip()
                    # Extract test names from bullet points or lists
                    for line in flaky_text.split('\n'):
                        # Remove bullet points, dashes, etc.
                        clean_line = re.sub(r'^[-*•\s]+', '', line.strip())
                        if clean_line and any(result["test_name"] in clean_line for result in results_summary):
                            # Extract just the test name if possible
                            test_name_match = re.search(r'(test_\w+)', clean_line)
                            if test_name_match:
                                flaky_tests.append(test_name_match.group(1))
                            else:
                                flaky_tests.append(clean_line)
                
                # Similar pattern for failing tests
                failing_match = re.search(r'(?:failing tests|Failing tests|consistently failing|Consistently failing):\s*(.*?)(?:\n\n|\n\d\.|\Z)', content, re.DOTALL)
                if failing_match:
                    failing_text = failing_match.group(1).strip()
                    for line in failing_text.split('\n'):
                        clean_line = re.sub(r'^[-*•\s]+', '', line.strip())
                        if clean_line and any(result["test_name"] in clean_line for result in results_summary):
                            test_name_match = re.search(r'(test_\w+)', clean_line)
                            if test_name_match:
                                failing_tests.append(test_name_match.group(1))
                            else:
                                failing_tests.append(clean_line)
                
                # If nothing could be extracted, identify patterns algorithmically
                if not (flaky_tests or failing_tests):
                    # Group tests by name
                    tests_by_name = {}
                    for result in results_summary:
                        test_name = result["test_name"]
                        if test_name not in tests_by_name:
                            tests_by_name[test_name] = []
                        tests_by_name[test_name].append(result)
                    
                    # Identify flaky and failing tests
                    for test_name, results in tests_by_name.items():
                        statuses = [r["status"] for r in results]
                        if "passed" in statuses and "failed" in statuses:
                            flaky_tests.append(test_name)
                        elif all(s == "failed" for s in statuses) and len(statuses) > 1:
                            failing_tests.append(test_name)
                
                return {
                    "status": "analysis_completed",
                    "message": "Pattern analysis using text parsing",
                    "flaky_tests": flaky_tests,
                    "failing_tests": failing_tests,
                    "slow_tests": slow_tests,
                    "correlations": correlations,
                    "other_patterns": other_patterns
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
        
        Please suggest specific improvements for each of these categories:
        1. Readability
        2. Maintainability
        3. Robustness
        4. Best practices
        5. Performance
        
        Format your response as a JSON object with these keys: readability, maintainability, 
        robustness, best_practices, performance.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test automation expert that suggests test improvements. Always output analysis in a structured JSON format with all the requested fields."},
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
                try:
                    result = json.loads(json_str)
                    # Ensure all expected fields are present
                    if not all(key in result for key in ["readability", "maintainability", "robustness", "best_practices", "performance"]):
                        logger.warning("AI response missing some expected fields")
                        # Add any missing fields
                        for field in ["readability", "maintainability", "robustness", "best_practices", "performance"]:
                            if field not in result:
                                result[field] = f"No suggestions for {field}"
                    return result
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {e}")
            
            # If JSON extraction fails, try to parse the whole content
            try:
                result = json.loads(content)
                # Ensure all expected fields are present
                for field in ["readability", "maintainability", "robustness", "best_practices", "performance"]:
                    if field not in result:
                        result[field] = f"No suggestions for {field}"
                return result
            except json.JSONDecodeError:
                # Extract suggestions using regex if JSON parsing fails
                logger.info("Using regex to extract suggestions from non-JSON response")
                
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
                
                # If none of the regex matches worked, use the whole content for readability
                if not any([readability_match, maintainability_match, robustness_match, 
                           best_practices_match, performance_match]):
                    logger.warning("Could not extract structured suggestions, using raw content")
                    return {
                        "readability": "AI output was not in expected format. Raw response: " + content[:200] + "...",
                        "maintainability": "See readability field for raw AI response",
                        "robustness": "See readability field for raw AI response",
                        "best_practices": "See readability field for raw AI response",
                        "performance": "See readability field for raw AI response"
                    }
                
                return {
                    "readability": readability,
                    "maintainability": maintainability,
                    "robustness": robustness,
                    "best_practices": best_practices,
                    "performance": performance
                }
        except Exception as e:
            logger.error(f"Error suggesting test improvements: {e}")
            # Ensure we return a dictionary with the expected fields
            return {
                "readability": f"Error: {str(e)}",
                "maintainability": "Analysis failed",
                "robustness": "Analysis failed",
                "best_practices": "Analysis failed",
                "performance": "Analysis failed",
                "status": "analysis_failed",
                "message": f"Failed to analyze test: {str(e)}",
                "suggestions": ["Review the test manually for potential improvements."]
            }
