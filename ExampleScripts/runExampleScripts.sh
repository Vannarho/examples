#!/usr/bin/env bash
set -e
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"
PYTHON_BIN="${PYTHON:-$(command -v python || command -v python3)}"
export PYTHONWARNINGS=ignore
status=0
return_code=0
tools_dir="../../../Tools/PythonTools"
expected_dir="./ExpectedOutput"
output_file="output.txt"
> "$output_file"

#dos2unix $expected_dir/*.txt

for file in *.py; do
    if [ -f "$file" ]; then
        > "$output_file"
        echo RUN $file  | tee -a "$output_file"
        # Append both stdout and stderr in a bash-3 compatible way
        "$PYTHON_BIN" "$file" >> "$output_file" 2>&1 || status=1
        return_code=$?
        if [ "$return_code" -gt "$status" ]; then
                status=$((status + return_code))
        fi

        if [ "$file" = "log.py" ]; then
            continue
        fi

        file_name="${file%.py}"
        "$PYTHON_BIN" "$tools_dir/compare_results.py" "txt" "$output_file" "$expected_dir/$file_name.txt"
        output_status=$?
        if [ "$output_status" -eq 0 ]; then
            echo "The output matches the expected output."
        else
            echo "The output differs from the expected output for $file_name."
            status=$((status + output_status))
        fi

    fi
done

python3 log.py || status=1

# clean up
rm -f "$output_file"
exit $status
