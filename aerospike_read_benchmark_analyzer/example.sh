#!/bin/bash
# Example script to run the Aerospike Read Benchmark Analysis

# Create output directory
mkdir -p example_output

# Run the complete analysis pipeline
echo "Running benchmark analysis..."
./analyze_benchmark.py \
  --data-dir . \
  --output-dir example_output \
  --json-file benchmark_data.json \
  --csv-file benchmark_summary.csv \
  --viz-dir visualizations \
  --report-file benchmark_report.html \
  --open-report

echo "Analysis complete! Results are in the example_output directory."
echo "Open example_output/benchmark_report.html to view the report."
