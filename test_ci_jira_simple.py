#!/usr/bin/env python3
"""Simple test to verify Jira is enabled in CI."""

import os
import sys

# Ensure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Simple CI Jira Test ===")
print(f"Current directory: {os.getcwd()}")
print(f".env exists: {os.path.exists('.env')}")

# Show raw environment variable
print(f"\nRaw env var JIRA_ENABLED: {os.getenv('JIRA_ENABLED')}")

# Import and check config
from config.config import Config

print(f"\nConfig.JIRA_ENABLED: {Config.JIRA_ENABLED}")
print(f"Type: {type(Config.JIRA_ENABLED)}")

if Config.JIRA_ENABLED:
    print("\n✅ SUCCESS: Jira is enabled!")
else:
    print("\n❌ FAIL: Jira is NOT enabled!")
    
    # Debug why
    print("\nDebugging:")
    print(f"- os.getenv('JIRA_ENABLED'): {os.getenv('JIRA_ENABLED')}")
    print(f"- os.getenv('JIRA_ENABLED', 'false'): {os.getenv('JIRA_ENABLED', 'false')}")
    print(f"- .lower(): {os.getenv('JIRA_ENABLED', 'false').lower()}")
    print(f"- == 'true': {os.getenv('JIRA_ENABLED', 'false').lower() == 'true'}")

# Test the actual pytest hook condition
print("\n=== Testing actual condition from conftest.py ===")
if Config.JIRA_ENABLED:
    print("✅ The condition 'if Config.JIRA_ENABLED:' is TRUE")
else:
    print("❌ The condition 'if Config.JIRA_ENABLED:' is FALSE")

# Exit with error if Jira is not enabled
sys.exit(0 if Config.JIRA_ENABLED else 1)