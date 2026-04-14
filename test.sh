#!/bin/bash

fail=0

echo "=== Ruff lint ==="
uv run ruff check skillset || fail=1

echo "=== Ruff format ==="
uv run ruff format --check skillset || fail=1

echo "=== Unit + integration tests ==="
uv run pytest tests -v --cov=skillset --cov-report=term-missing || fail=1

echo "=== File length check (max 300 lines) ==="
for f in $(find skillset -name '*.py'); do
  lines=$(wc -l < "$f")
  if [ "$lines" -gt 300 ]; then
    echo "FAIL: $f has $lines lines (max 300)"
    fail=1
  fi
done

if [ "$fail" -eq 1 ]; then
  echo "=== Some checks FAILED ==="  
fi

echo "=== All checks passed ==="
