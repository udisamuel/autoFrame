#!/usr/bin/env python
import argparse
import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from config.config import Config

def main():
    parser = argparse.ArgumentParser(description="AI Capabilities CLI for autoFrame")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Generate test data
    gen_data_parser = subparsers.add_parser("generate-data", help="Generate test data")
    gen_data_parser.add_argument("--type", choices=["user", "api", "form", "dataset"], required=True, help="Type of data to generate")
    gen_data_parser.add_argument("--output", help="Output file path")
    gen_data_parser.add_argument("--count", type=int, default=1, help="Number of items to generate")
    gen_data_parser.add_argument("--endpoint", help="API endpoint (for API data generation)")
    gen_data_parser.add_argument("--method", default="POST", help="HTTP method (for API data generation)")
    gen_data_parser.add_argument("--form-name", help="Form name (for form data generation)")
    gen_data_parser.add_argument("--fields", help="Comma-separated list of field names (for form data generation)")
    gen_data_parser.add_argument("--constraints", help="JSON string of constraints")
    
    # Generate test
    gen_test_parser = subparsers.add_parser("generate-test", help="Generate a test case")
    gen_test_parser.add_argument("--type", choices=["api", "ui", "db"], required=True, help="Type of test to generate")
    gen_test_parser.add_argument("--output", help="Output file path")
    gen_test_parser.add_argument("--description", required=True, help="Test description")
    gen_test_parser.add_argument("--endpoint", help="API endpoint (for API test generation)")
    gen_test_parser.add_argument("--method", default="GET", help="HTTP method (for API test generation)")
    gen_test_parser.add_argument("--page-name", help="Page name (for UI test generation)")
    gen_test_parser.add_argument("--steps", help="Comma-separated list of test steps (for UI test generation)")
    gen_test_parser.add_argument("--db-type", choices=["postgres", "clickhouse"], help="Database type (for DB test generation)")
    gen_test_parser.add_argument("--query", help="SQL query (for DB test generation)")
    
    # Analyze test
    analyze_parser = subparsers.add_parser("analyze-test", help="Analyze test code and suggest improvements")
    analyze_parser.add_argument("--file", required=True, help="Path to test file")
    analyze_parser.add_argument("--output", help="Output file path for analysis report")
    
    # Analyze failure
    failure_parser = subparsers.add_parser("analyze-failure", help="Analyze a test failure")
    failure_parser.add_argument("--test-name", required=True, help="Name of the failed test")
    failure_parser.add_argument("--error", required=True, help="Error message from the failure")
    failure_parser.add_argument("--test-file", required=True, help="Path to the test file")
    failure_parser.add_argument("--screenshot", help="Path to failure screenshot (for UI tests)")
    failure_parser.add_argument("--response", help="Path to response data file (for API tests)")
    failure_parser.add_argument("--output", help="Output file path for analysis report")
    
    args = parser.parse_args()
    
    # Check if AI features are enabled
    if not Config.AI_FEATURES_ENABLED:
        print("AI features are disabled. Enable them by setting AI_FEATURES_ENABLED=true in your .env file.")
        return
    
    # Check if OpenAI API key is configured
    if not Config.OPENAI_API_KEY:
        print("OpenAI API key is not configured. Set OPENAI_API_KEY in your .env file.")
        return
    
    if args.command == "generate-data":
        from utils.ai_data_generator import AIDataGenerator
        generator = AIDataGenerator()
        
        constraints = {}
        if args.constraints:
            try:
                constraints = json.loads(args.constraints)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in constraints: {args.constraints}")
                return
        
        if args.type == "user":
            results = []
            for _ in range(args.count):
                results.append(generator.generate_user_profile(constraints))
        elif args.type == "api":
            if not args.endpoint:
                print("Error: --endpoint is required for API data generation")
                return
            
            results = []
            for _ in range(args.count):
                results.append(generator.generate_api_payload(args.endpoint, args.method, constraints))
        elif args.type == "form":
            if not args.form_name or not args.fields:
                print("Error: --form-name and --fields are required for form data generation")
                return
            
            fields = [field.strip() for field in args.fields.split(',')]
            results = []
            for _ in range(args.count):
                results.append(generator.generate_form_data(args.form_name, fields))
        elif args.type == "dataset":
            if not args.fields:
                print("Error: --fields is required for dataset generation")
                return
                
            data_type = args.fields  # In this case, fields parameter is used to specify dataset type
            results = generator.generate_test_data_set(data_type, args.count, constraints)
                
        if args.output:
            os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Data saved to {args.output}")
        else:
            print(json.dumps(results, indent=2))
            
    elif args.command == "generate-test":
        from utils.ai_test_generator import AITestGenerator
        generator = AITestGenerator()
        
        if args.type == "api":
            if not args.endpoint:
                print("Error: --endpoint is required for API test generation")
                return
                
            code = generator.generate_api_test(args.endpoint, args.method, args.description)
            file_name = args.output or f"test_{args.method.lower()}_{args.endpoint.replace('/', '_').strip('_')}.py"
            
        elif args.type == "ui":
            if not args.page_name:
                print("Error: --page-name is required for UI test generation")
                return
                
            if not args.steps:
                print("Error: --steps is required for UI test generation")
                return
                
            steps = [step.strip() for step in args.steps.split(',')]
            code = generator.generate_ui_test(args.page_name, args.description, steps)
            file_name = args.output or f"test_{args.page_name.lower()}.py"
            
        elif args.type == "db":
            if not args.db_type or not args.query:
                print("Error: --db-type and --query are required for DB test generation")
                return
                
            code = generator.generate_db_test(args.db_type, args.query, args.description)
            file_name = args.output or f"test_db_{args.db_type.lower()}.py"
        
        # Save the generated test
        if not file_name.startswith(os.sep):
            file_name = os.path.join("tests", file_name)
            
        file_path = generator.save_test_to_file(code, os.path.basename(file_name), os.path.dirname(file_name))
        print(f"Test saved to {file_path}")
        
    elif args.command == "analyze-test":
        from utils.ai_test_analyzer import AITestAnalyzer
        analyzer = AITestAnalyzer()
        
        # Read the test file
        try:
            with open(args.file, 'r') as f:
                test_code = f.read()
        except Exception as e:
            print(f"Error reading test file: {e}")
            return
            
        # Analyze the test code
        suggestions = analyzer.suggest_test_improvements(test_code)
        
        if args.output:
            os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
            with open(args.output, 'w') as f:
                json.dump(suggestions, f, indent=2)
            print(f"Analysis saved to {args.output}")
        else:
            print(json.dumps(suggestions, indent=2))
            
    elif args.command == "analyze-failure":
        from utils.ai_test_analyzer import AITestAnalyzer
        analyzer = AITestAnalyzer()
        
        # Read the test file
        try:
            with open(args.test_file, 'r') as f:
                test_code = f.read()
        except Exception as e:
            print(f"Error reading test file: {e}")
            return
            
        # Read response data if provided
        response_data = None
        if args.response:
            try:
                with open(args.response, 'r') as f:
                    content = f.read()
                    try:
                        response_data = json.loads(content)
                    except json.JSONDecodeError:
                        response_data = content
            except Exception as e:
                print(f"Warning: Error reading response data file: {e}")
        
        # Analyze the failure
        analysis = analyzer.analyze_test_failure(
            args.test_name,
            args.error,
            test_code,
            args.screenshot,
            response_data
        )
        
        if args.output:
            os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"Analysis saved to {args.output}")
        else:
            print(json.dumps(analysis, indent=2))
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
