import logging
import json
import requests
from typing import Dict, Any, Optional, Union, List
import allure
from config.config import Config
import time

logger = logging.getLogger(__name__)

class APIHelper:
    """
    Helper class for API testing that provides enhanced functionality for HTTP requests,
    response validation, and reporting.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the API helper with optional base URL.
        
        Args:
            base_url: The base URL for API requests. Defaults to Config.BASE_URL if not provided.
        """
        self.base_url = base_url or Config.BASE_URL
        self.session = requests.Session()
        self.timeout = Config.DEFAULT_TIMEOUT / 1000  # Convert from ms to seconds
    
    def _construct_url(self, endpoint: str) -> str:
        """
        Construct the full URL by combining the base URL and endpoint.
        
        Args:
            endpoint: The API endpoint
            
        Returns:
            The full URL
        """
        # If endpoint already starts with http/https, return as is
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        
        # Make sure endpoint starts with / for proper joining
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'
            
        return f"{self.base_url}{endpoint}"
    
    def _log_request(self, method: str, url: str, headers: Dict[str, str], 
                     params: Optional[Dict[str, Any]] = None, 
                     data: Optional[Any] = None, 
                     json_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log the request details.
        
        Args:
            method: The HTTP method
            url: The request URL
            headers: The request headers
            params: The query parameters
            data: The request data
            json_data: The JSON payload
        """
        sanitized_headers = self._sanitize_headers(headers)
        
        with allure.step(f"API Request: {method} {url}"):
            logger.info(f"Request: {method} {url}")
            logger.debug(f"Headers: {sanitized_headers}")
            if params:
                logger.debug(f"Query Params: {params}")
            if data:
                logger.debug(f"Data: {data}")
            if json_data:
                logger.debug(f"JSON: {json_data}")
            
            allure.attach(
                f"URL: {url}\n"
                f"Method: {method}\n"
                f"Headers: {json.dumps(sanitized_headers, indent=2)}\n"
                f"Params: {json.dumps(params, indent=2) if params else 'None'}\n"
                f"Data: {data if data else 'None'}\n"
                f"JSON: {json.dumps(json_data, indent=2) if json_data else 'None'}",
                name="Request Details",
                attachment_type=allure.attachment_type.TEXT
            )
    
    def _log_response(self, response: requests.Response, elapsed_time: float) -> None:
        """
        Log the response details.
        
        Args:
            response: The response object
            elapsed_time: The elapsed time in seconds
        """
        status_code = response.status_code
        reason = response.reason
        
        with allure.step(f"API Response: {status_code} {reason} ({elapsed_time:.2f}s)"):
            logger.info(f"Response: {status_code} {reason} ({elapsed_time:.2f}s)")
            
            try:
                response_body = response.json()
                logger.debug(f"Response JSON: {response_body}")
                response_body_str = json.dumps(response_body, indent=2)
            except:
                response_body = response.text
                logger.debug(f"Response Text: {response_body}")
                response_body_str = response_body
            
            allure.attach(
                f"Status: {status_code} {reason}\n"
                f"Elapsed Time: {elapsed_time:.2f}s\n"
                f"Headers: {json.dumps(dict(response.headers), indent=2)}\n"
                f"Body: {response_body_str}",
                name="Response Details",
                attachment_type=allure.attachment_type.TEXT
            )
            
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Sanitize sensitive information in headers.
        
        Args:
            headers: The request headers
            
        Returns:
            Sanitized headers with masked sensitive values
        """
        sensitive_headers = ['authorization', 'x-api-key', 'api-key', 'token', 'password']
        sanitized = {}
        
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = '********'
            else:
                sanitized[key] = value
                
        return sanitized
    
    def request(self, method: str, endpoint: str, 
                headers: Optional[Dict[str, str]] = None,
                params: Optional[Dict[str, Any]] = None,
                data: Optional[Any] = None,
                json_data: Optional[Dict[str, Any]] = None,
                files: Optional[Dict[str, Any]] = None,
                auth: Optional[Any] = None,
                timeout: Optional[float] = None,
                allow_redirects: bool = True,
                verify: bool = True) -> requests.Response:
        """
        Send an HTTP request.
        
        Args:
            method: The HTTP method
            endpoint: The API endpoint
            headers: The request headers
            params: The query parameters
            data: The request data
            json_data: The JSON payload
            files: Files to upload
            auth: Authentication
            timeout: Request timeout in seconds
            allow_redirects: Whether to allow redirects
            verify: Whether to verify SSL certificates
            
        Returns:
            The response object
        """
        url = self._construct_url(endpoint)
        headers = headers or {}
        actual_timeout = timeout or self.timeout
        
        self._log_request(method, url, headers, params, data, json_data)
        
        start_time = time.time()
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                files=files,
                auth=auth,
                timeout=actual_timeout,
                allow_redirects=allow_redirects,
                verify=verify
            )
        except Exception as e:
            logger.exception(f"Request failed: {str(e)}")
            allure.attach(
                f"Request failed: {str(e)}",
                name="Request Error",
                attachment_type=allure.attachment_type.TEXT
            )
            raise
        
        elapsed_time = time.time() - start_time
        self._log_response(response, elapsed_time)
        
        return response
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Send a GET request.
        
        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments to pass to request()
            
        Returns:
            The response object
        """
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Send a POST request.
        
        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments to pass to request()
            
        Returns:
            The response object
        """
        return self.request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Send a PUT request.
        
        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments to pass to request()
            
        Returns:
            The response object
        """
        return self.request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Send a DELETE request.
        
        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments to pass to request()
            
        Returns:
            The response object
        """
        return self.request('DELETE', endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Send a PATCH request.
        
        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments to pass to request()
            
        Returns:
            The response object
        """
        return self.request('PATCH', endpoint, **kwargs)
    
    def head(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Send a HEAD request.
        
        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments to pass to request()
            
        Returns:
            The response object
        """
        return self.request('HEAD', endpoint, **kwargs)
    
    def options(self, endpoint: str, **kwargs) -> requests.Response:
        """
        Send an OPTIONS request.
        
        Args:
            endpoint: The API endpoint
            **kwargs: Additional arguments to pass to request()
            
        Returns:
            The response object
        """
        return self.request('OPTIONS', endpoint, **kwargs)

class APIAssert:
    """
    Helper class for API response assertions.
    """
    
    @staticmethod
    def status_code(response: requests.Response, expected_code: int) -> None:
        """
        Assert the response status code.
        
        Args:
            response: The response object
            expected_code: The expected status code
        """
        actual_code = response.status_code
        with allure.step(f"Assert status code is {expected_code}"):
            assert actual_code == expected_code, f"Expected status code {expected_code}, got {actual_code}"
    
    @staticmethod
    def status_code_in(response: requests.Response, expected_codes: List[int]) -> None:
        """
        Assert the response status code is in a list of expected codes.
        
        Args:
            response: The response object
            expected_codes: List of expected status codes
        """
        actual_code = response.status_code
        with allure.step(f"Assert status code is in {expected_codes}"):
            assert actual_code in expected_codes, f"Expected status code to be in {expected_codes}, got {actual_code}"
    
    @staticmethod
    def json_body(response: requests.Response) -> Dict[str, Any]:
        """
        Assert the response has a valid JSON body and return it.
        
        Args:
            response: The response object
            
        Returns:
            The response JSON as a dictionary
        """
        with allure.step("Assert response has valid JSON body"):
            try:
                body = response.json()
                return body
            except Exception as e:
                error_message = f"Response does not contain a valid JSON body: {str(e)}"
                allure.attach(
                    response.text,
                    name="Invalid JSON Response",
                    attachment_type=allure.attachment_type.TEXT
                )
                assert False, error_message
    
    @staticmethod
    def json_has_key(response: requests.Response, key: str) -> Any:
        """
        Assert the response JSON has a specific key and return its value.
        
        Args:
            response: The response object
            key: The key to check for
            
        Returns:
            The value of the key
        """
        body = APIAssert.json_body(response)
        with allure.step(f"Assert JSON has key '{key}'"):
            assert key in body, f"Expected key '{key}' not found in response JSON"
            return body[key]
    
    @staticmethod
    def json_key_equals(response: requests.Response, key: str, expected_value: Any) -> None:
        """
        Assert a key in the response JSON equals a specific value.
        
        Args:
            response: The response object
            key: The key to check
            expected_value: The expected value
        """
        value = APIAssert.json_has_key(response, key)
        with allure.step(f"Assert JSON key '{key}' equals '{expected_value}'"):
            assert value == expected_value, f"Expected '{key}' to be '{expected_value}', got '{value}'"
    
    @staticmethod
    def json_key_contains(response: requests.Response, key: str, expected_value: Any) -> None:
        """
        Assert a key in the response JSON contains a specific value.
        
        Args:
            response: The response object
            key: The key to check
            expected_value: The expected value to be contained
        """
        value = APIAssert.json_has_key(response, key)
        with allure.step(f"Assert JSON key '{key}' contains '{expected_value}'"):
            assert expected_value in value, f"Expected '{key}' to contain '{expected_value}', got '{value}'"
    
    @staticmethod
    def json_has_structure(response: requests.Response, structure: Dict[str, Any]) -> None:
        """
        Assert the response JSON has a specific structure (keys and optional value types).
        
        For each key in structure:
        - If value is None, only check that key exists
        - If value is a type (e.g., str, int), check that key exists and value is of that type
        - If value is a dict, recursively check that structure
        
        Args:
            response: The response object
            structure: The expected structure
        """
        body = APIAssert.json_body(response)
        
        with allure.step("Assert JSON has expected structure"):
            APIAssert._check_structure(body, structure, [])
    
    @staticmethod
    def _check_structure(data: Any, structure: Dict[str, Any], path: List[str]) -> None:
        """
        Recursively check the structure of a JSON object.
        
        Args:
            data: The data to check
            structure: The expected structure
            path: The current path in the JSON object (for error reporting)
        """
        for key, expected in structure.items():
            current_path = path + [key]
            path_str = '.'.join(current_path) if current_path else 'root'
            
            # Check if key exists
            assert key in data, f"Expected key '{key}' at '{path_str}' not found"
            
            if expected is None:
                # Only check existence
                continue
                
            elif isinstance(expected, type):
                # Check type
                assert isinstance(data[key], expected), \
                    f"Expected '{path_str}' to be of type {expected.__name__}, " \
                    f"got {type(data[key]).__name__}"
                    
            elif isinstance(expected, dict):
                # Check nested structure
                assert isinstance(data[key], dict), \
                    f"Expected '{path_str}' to be a dictionary, got {type(data[key]).__name__}"
                APIAssert._check_structure(data[key], expected, current_path)
            
            else:
                # Direct value comparison
                assert data[key] == expected, \
                    f"Expected '{path_str}' to be {expected}, got {data[key]}"

    @staticmethod
    def header_exists(response: requests.Response, header: str) -> str:
        """
        Assert a specific header exists in the response.
        
        Args:
            response: The response object
            header: The header name (case-insensitive)
            
        Returns:
            The header value
        """
        with allure.step(f"Assert header '{header}' exists"):
            # Headers in requests are case-insensitive
            headers = {k.lower(): v for k, v in response.headers.items()}
            header_lower = header.lower()
            
            assert header_lower in headers, f"Expected header '{header}' not found in response"
            return headers[header_lower]
    
    @staticmethod
    def header_equals(response: requests.Response, header: str, expected_value: str) -> None:
        """
        Assert a response header equals a specific value.
        
        Args:
            response: The response object
            header: The header name (case-insensitive)
            expected_value: The expected header value
        """
        value = APIAssert.header_exists(response, header)
        with allure.step(f"Assert header '{header}' equals '{expected_value}'"):
            assert value == expected_value, f"Expected header '{header}' to be '{expected_value}', got '{value}'"
    
    @staticmethod
    def header_contains(response: requests.Response, header: str, expected_value: str) -> None:
        """
        Assert a response header contains a specific value.
        
        Args:
            response: The response object
            header: The header name (case-insensitive)
            expected_value: The expected value to be contained
        """
        value = APIAssert.header_exists(response, header)
        with allure.step(f"Assert header '{header}' contains '{expected_value}'"):
            assert expected_value in value, f"Expected header '{header}' to contain '{expected_value}', got '{value}'"
    
    @staticmethod
    def response_time(response: requests.Response, max_time: float) -> None:
        """
        Assert the response time is less than a maximum value.
        
        Args:
            response: The response object
            max_time: The maximum response time in seconds
        """
        time_taken = response.elapsed.total_seconds()
        with allure.step(f"Assert response time is less than {max_time}s"):
            assert time_taken <= max_time, f"Expected response time to be <= {max_time}s, got {time_taken}s"
