#!/usr/bin/env python3
"""Debug script to check Jira configuration in CI/CD."""

import os
import sys
from pathlib import Path

print("=== CI/CD Jira Debug Script ===\n")

# Check current directory
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

# Check if .env file exists
env_file = Path(".env")
print(f"\n.env file exists: {env_file.exists()}")
if env_file.exists():
    print(".env file contents:")
    print("-" * 40)
    with open(".env", "r") as f:
        contents = f.read()
        # Mask sensitive data
        lines = contents.split('\n')
        for line in lines:
            if 'TOKEN' in line or 'PASSWORD' in line:
                key = line.split('=')[0] if '=' in line else line
                print(f"{key}=***MASKED***")
            else:
                print(line)
    print("-" * 40)

# Check environment variables
print("\nEnvironment variables:")
env_vars = [
    "CI", "GITHUB_ACTIONS", "JIRA_ENABLED", "JIRA_BASE_URL",
    "JIRA_USERNAME", "JIRA_PROJECT_KEY", "JIRA_API_TOKEN"
]
for var in env_vars:
    value = os.getenv(var)
    if var == "JIRA_API_TOKEN" and value:
        print(f"{var}=***MASKED***")
    else:
        print(f"{var}={value}")

# Load configuration
print("\nLoading configuration...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config.config import Config
    print("\nConfig values:")
    print(f"Config.JIRA_ENABLED: {Config.JIRA_ENABLED} (type: {type(Config.JIRA_ENABLED)})")
    print(f"Config.JIRA_BASE_URL: {Config.JIRA_BASE_URL}")
    print(f"Config.JIRA_PROJECT_KEY: {Config.JIRA_PROJECT_KEY}")
    print(f"Config.JIRA_USERNAME: {Config.JIRA_USERNAME}")
    print(f"Config.JIRA_API_TOKEN: {'***SET***' if Config.JIRA_API_TOKEN else 'NOT SET'}")
    
    # Test the condition that enables Jira
    print(f"\nJira should be enabled: {Config.JIRA_ENABLED == True}")
    print(f"Type check: {type(Config.JIRA_ENABLED)}")
    
except Exception as e:
    print(f"Error loading config: {e}")
    import traceback
    traceback.print_exc()

# Test dotenv loading
print("\nTesting python-dotenv...")
try:
    from dotenv import load_dotenv, dotenv_values
    
    # Show what dotenv sees
    values = dotenv_values()
    print(f"Dotenv found {len(values)} values")
    if "JIRA_ENABLED" in values:
        print(f"JIRA_ENABLED from dotenv: {values['JIRA_ENABLED']}")
    
    # Try loading with override
    load_dotenv(override=True)
    print(f"After load_dotenv(override=True): JIRA_ENABLED={os.getenv('JIRA_ENABLED')}")
    
except Exception as e:
    print(f"Error with dotenv: {e}")

print("\n=== End Debug ===")