#!/bin/bash

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Define report directories
ALLURE_RESULTS_DIR="reports/allure-results"
ALLURE_REPORT_DIR="reports/allure-report"

# Get absolute paths for cleaner outputs
ABSOLUTE_REPORT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/reports/allure-report"

# Clean previous results
rm -rf ${ALLURE_RESULTS_DIR}
rm -rf ${ALLURE_REPORT_DIR}
mkdir -p ${ALLURE_RESULTS_DIR}
mkdir -p ${ALLURE_REPORT_DIR}

# Check if Xray reporting is enabled
if [ "$XRAY_REPORTING" == "true" ]; then
    echo "Xray reporting is enabled"
    XRAY_ARGS="--xray"
else
    XRAY_ARGS=""
fi

# Run tests with Allure reporting and parallel execution
# By default, use number of CPUs - 1 for parallel execution
NUM_CPUS=$(python -c 'import os; print(max(1, os.cpu_count() - 1))')

# Check if a specific number of workers was provided, otherwise use calculated value
if [[ "$*" == *"-n"* ]] || [[ "$*" == *"--numprocesses"* ]]; then
    # User specified number of workers, just pass all args through
    python -m pytest tests "$@" --alluredir=${ALLURE_RESULTS_DIR} ${XRAY_ARGS}
else
    # User didn't specify worker count, use our calculated value
    python -m pytest tests -n ${NUM_CPUS} "$@" --alluredir=${ALLURE_RESULTS_DIR} ${XRAY_ARGS}
fi

# Check if the tests ran successfully
if [ $? -eq 0 ]; then
    echo "Tests completed successfully!"
else
    echo "Tests completed with failures!"
fi

# Check for screenshots and copy them to Allure results if needed
SCREENSHOTS_DIR="reports/screenshots"
if [ -d "${SCREENSHOTS_DIR}" ]; then
    echo "Found screenshots in ${SCREENSHOTS_DIR}"
    # Copy all screenshots to Allure results directory to ensure they're included
    cp -v ${SCREENSHOTS_DIR}/*.png ${ALLURE_RESULTS_DIR}/ 2>/dev/null || echo "No screenshots found to copy"
else
    echo "No screenshots directory found"
fi

# Generate Allure report
echo "Generating Allure report..."
allure generate ${ALLURE_RESULTS_DIR} -o ${ALLURE_REPORT_DIR} --clean

# Keep the Allure results directory for debugging
echo "Preserving Allure results in ${ALLURE_RESULTS_DIR}"

echo "Report generated successfully!"
echo "You can view the report by opening: ${ALLURE_REPORT_DIR}/index.html"

