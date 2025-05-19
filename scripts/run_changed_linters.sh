#!/usr/bin/env bash
set -euo pipefail

changed_files=$(git diff --cached --name-only --diff-filter=ACM)

python_changed=false
frontend_changed=false

for file in $changed_files; do
    top_dir="${file%%/*}"
    case "$top_dir" in
        backend|scraper|common)
            python_changed=true
            ;;
        frontend)
            frontend_changed=true
            ;;
        *)
            if [[ "$file" == "setup.py" ]]; then
                python_changed=true
            fi
            ;;
    esac
    if [[ "$python_changed" = true && "$frontend_changed" = true ]]; then
        break
    fi
done

if [[ "$python_changed" = false && "$frontend_changed" = false ]]; then
    echo "No linting required."
    exit 0
fi

if [[ "$python_changed" = true ]]; then
    echo "Running black..."
    black --check backend scraper common setup.py
fi

if [[ "$frontend_changed" = true ]]; then
    echo "Running ESLint..."
    npm run lint --prefix frontend
fi
