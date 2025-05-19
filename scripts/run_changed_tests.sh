#!/usr/bin/env bash
set -euo pipefail

# Get list of staged files
changed_files=$(git diff --cached --name-only --diff-filter=ACM)

# Determine unique top-level directories that contain tests
dirs_to_test=()
for file in $changed_files; do
    dir=${file%%/*}
    # Skip if file is at repo root
    if [[ "$file" == "$dir" ]]; then
        continue
    fi
    if [ -d "$dir" ]; then
        # Check for python test files in directory
        if find "$dir" -name 'test_*.py' -o -name '*_test.py' | grep -q .; then
            if [[ ! " ${dirs_to_test[*]} " =~ " $dir " ]]; then
                dirs_to_test+=("$dir")
            fi
        fi
    fi
done

if [ ${#dirs_to_test[@]} -eq 0 ]; then
    echo "No tests to run."
    exit 0
fi

for dir in "${dirs_to_test[@]}"; do
    echo "Running tests in $dir"
    pytest "$dir"

done
