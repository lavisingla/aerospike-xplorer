#!/usr/bin/env python3
"""
Analyze Aerospike write benchmark data.

This script orchestrates the entire analysis pipeline from data extraction
to report generation.
"""

import os
import argparse
import webbrowser
from extract_benchmark_data import extract_benchmark_data
from visualize_benchmark_data import visualize_benchmark_data
from generate_benchmark_report import generate_report


def analyze_benchmark(data_dir, output_dir, json_file, csv_file, viz_dir, report_file, open_report):
    """
    Run the complete benchmark analysis pipeline.
    
    Args:
        data_dir: Directory containing benchmark data
        output_dir: Directory for output files
        json_file: Output JSON file name
        csv_file: Output CSV file name
        viz_dir: Directory for visualizations
        report_file: Output HTML report file name
        open_report: Whether to open the HTML report in the default browser
    """
    print("=" * 80)
    print("Aerospike Write Benchmark Analysis")
    print("=" * 80)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Extract benchmark data
    print("\nStep 1: Extracting benchmark data...")
    benchmark_data = extract_benchmark_data(data_dir, output_dir, json_file, csv_file)
    
    # Step 2: Generate visualizations
    print("\nStep 2: Generating visualizations...")
    viz_path = os.path.join(output_dir, viz_dir)
    os.makedirs(viz_path, exist_ok=True)
    visualize_benchmark_data(benchmark_data, output_dir, viz_path)
    
    # Step 3: Generate HTML report
    print("\nStep 3: Generating HTML report...")
    generate_report(benchmark_data, output_dir, report_file, viz_dir, open_report)
    
    print("\nAnalysis complete!")
    print(f"- Benchmark data saved to: {os.path.join(output_dir, json_file)}")
    print(f"- Summary statistics saved to: {os.path.join(output_dir, csv_file)}")
    print(f"- Visualizations saved to: {os.path.join(output_dir, viz_dir)}")
    print(f"- HTML report saved to: {os.path.join(output_dir, report_file)}")
    
    if open_report:
        print("\nOpening HTML report in browser...")
    else:
        print(f"\nTo view the report, open: {os.path.join(output_dir, report_file)}")


def main():
    """Main function to run the benchmark analysis."""
    parser = argparse.ArgumentParser(description='Analyze Aerospike write benchmark data')
    parser.add_argument('--data-dir', default='.', help='Directory containing benchmark data')
    parser.add_argument('--output-dir', default='benchmark_analysis', help='Directory for output files')
    parser.add_argument('--json-file', default='benchmark_data.json', help='Output JSON file name')
    parser.add_argument('--csv-file', default='benchmark_summary.csv', help='Output CSV file name')
    parser.add_argument('--viz-dir', default='visualizations', help='Directory for visualizations')
    parser.add_argument('--report-file', default='benchmark_report.html', help='Output HTML report file name')
    parser.add_argument('--open-report', action='store_true', help='Open the HTML report in the default browser')
    args = parser.parse_args()
    
    analyze_benchmark(
        args.data_dir,
        args.output_dir,
        args.json_file,
        args.csv_file,
        args.viz_dir,
        args.report_file,
        args.open_report
    )


if __name__ == '__main__':
    main()
