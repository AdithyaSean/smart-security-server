#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print success/failure
print_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

# Test Python version
echo "Testing Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ "$python_version" == 3.12* ]]; then
    echo -e "${GREEN}✓ Python 3.12 found ($python_version)${NC}"
else
    echo -e "${RED}✗ Python 3.12 not found (found $python_version)${NC}"
    exit 1
fi

# Test installation script
echo "Testing installation script..."
./run.sh test
print_result "Installation test"

# All tests passed
echo -e "\n${GREEN}All tests passed successfully!${NC}"
