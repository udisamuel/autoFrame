#!/usr/bin/env python3
"""
Script to run Locust performance tests with various configurations.
"""
import os
import sys
import argparse
import subprocess
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Run Locust performance tests")
    parser.add_argument(
        "--test", "-t", 
        default="example_test.py",
        help="Test file to run (from locustfiles directory)"
    )
    parser.add_argument(
        "--users", "-u", 
        type=int, 
        default=10,
        help="Number of concurrent users"
    )
    parser.add_argument(
        "--spawn-rate", "-r", 
        type=int, 
        default=1,
        help="Rate to spawn users at (users per second)"
    )
    parser.add_argument(
        "--run-time", "-d", 
        default="1m",
        help="Duration to run the test for (e.g. 30s, 5m, 1h)"
    )
    parser.add_argument(
        "--host", 
        default=None,
        help="Host to run tests against (overrides the one defined in the locustfile)"
    )
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="Run in headless mode (no web UI)"
    )
    
    args = parser.parse_args()
    
    # Create timestamp for reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure the test file exists
    test_path = os.path.join("locustfiles", args.test)
    if not os.path.exists(test_path):
        print(f"Error: Test file '{test_path}' not found.")
        sys.exit(1)
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Build command
    cmd = ["locust", "-f", test_path]
    
    if args.headless:
        cmd.extend([
            "--headless",
            "--users", str(args.users),
            "--spawn-rate", str(args.spawn_rate),
            "--run-time", args.run_time,
            "--html", f"reports/report_{timestamp}.html",
            "--csv", f"reports/report_{timestamp}"
        ])
    
    if args.host:
        cmd.extend(["--host", args.host])
    
    # Run the command
    try:
        print(f"Starting Locust with command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Locust: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Test interrupted by user.")
    
    if args.headless:
        print(f"Test completed. Reports saved to reports/report_{timestamp}.html and reports/report_{timestamp}.csv")
    else:
        print("Test completed.")

if __name__ == "__main__":
    main()
