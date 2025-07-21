#!/usr/bin/env python3
"""
Aerospike Read Benchmark Analysis

This script runs the complete benchmark analysis pipeline:
1. Extract data from benchmark files
2. Generate visualizations
3. Create a comprehensive HTML report

Usage:
  python analyze_benchmark.py [options]

Options:
  --data-dir DIR         Directory containing benchmark data (default: current directory)
  --output-dir DIR       Directory for output files (default: 'benchmark_analysis')
  --json-file FILE       Output JSON file name (default: 'benchmark_data.json')
  --csv-file FILE        Output CSV file name (default: 'benchmark_summary.csv')
  --viz-dir DIR          Directory for visualizations (default: 'visualizations')
  --report-file FILE     Output HTML report file name (default: 'benchmark_report.html')
  --open-report          Open the HTML report in the default browser after generation
"""

import os
import sys
import argparse
import subprocess
import webbrowser
from datetime import datetime

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Analyze Aerospike read benchmark data')
    
    parser.add_argument('--data-dir', default='.',
                        help='Directory containing benchmark data (default: current directory)')
    parser.add_argument('--output-dir', default='benchmark_analysis',
                        help='Directory for output files (default: benchmark_analysis)')
    parser.add_argument('--json-file', default='benchmark_data.json',
                        help='Output JSON file name (default: benchmark_data.json)')
    parser.add_argument('--csv-file', default='benchmark_summary.csv',
                        help='Output CSV file name (default: benchmark_summary.csv)')
    parser.add_argument('--viz-dir', default='visualizations',
                        help='Directory for visualizations (default: visualizations)')
    parser.add_argument('--report-file', default='benchmark_report.html',
                        help='Output HTML report file name (default: benchmark_report.html)')
    parser.add_argument('--open-report', action='store_true',
                        help='Open the HTML report in the default browser after generation')
    
    return parser.parse_args()

def run_extraction(args):
    """Run the data extraction script."""
    print("\n" + "="*80)
    print("STEP 1: Extracting benchmark data")
    print("="*80)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Construct paths
    json_path = os.path.join(args.output_dir, args.json_file)
    csv_path = os.path.join(args.output_dir, args.csv_file)
    
    # Import the extraction module
    sys.path.insert(0, '.')
    from extract_benchmark_data import BenchmarkDataExtractor
    
    # Run extraction
    print(f"Extracting data from {args.data_dir}...")
    extractor = BenchmarkDataExtractor(base_dir=args.data_dir)
    
    # Save to JSON
    print(f"Saving data to {json_path}...")
    extractor.save_to_json(json_path)
    
    # Save to CSV
    print(f"Saving summary to {csv_path}...")
    extractor.save_summary_to_csv(csv_path)
    
    # Create DataFrames for analysis
    print("Creating DataFrames for analysis...")
    dataframes = extractor.create_dataframes()
    
    # Print some basic statistics
    summary_df = dataframes['summary']
    print("\nBenchmark Summary Statistics:")
    print(f"Total configurations tested: {len(summary_df)}")
    print(f"Average TPS across all tests: {summary_df['avg_tps'].mean():.2f}")
    print(f"Maximum TPS achieved: {summary_df['max_tps'].max()} (configuration: {summary_df.loc[summary_df['max_tps'].idxmax()][['percentage', 'size_kb', 'threads']].to_dict()})")
    print(f"Minimum p99 latency: {summary_df['avg_p99_us'].min():.2f} μs (configuration: {summary_df.loc[summary_df['avg_p99_us'].idxmin()][['percentage', 'size_kb', 'threads']].to_dict()})")
    
    return json_path, csv_path

def run_visualization(args, json_path, csv_path):
    """Run the visualization script."""
    print("\n" + "="*80)
    print("STEP 2: Generating visualizations")
    print("="*80)
    
    # Construct paths
    viz_dir = os.path.join(args.output_dir, args.viz_dir)
    
    # Create visualization directory if it doesn't exist
    os.makedirs(viz_dir, exist_ok=True)
    
    # Import the visualization module
    sys.path.insert(0, '.')
    from visualize_benchmark_data import BenchmarkVisualizer
    
    # Run visualization
    print(f"Generating visualizations in {viz_dir}...")
    visualizer = BenchmarkVisualizer(data_file=json_path, summary_file=csv_path, output_dir=viz_dir)
    visualizer.generate_all_visualizations()
    
    return viz_dir

def run_report_generation(args, json_path, csv_path, viz_dir):
    """Run the report generation script."""
    print("\n" + "="*80)
    print("STEP 3: Generating HTML report")
    print("="*80)
    
    # Construct paths
    report_path = os.path.join(args.output_dir, args.report_file)
    
    # Import the report generation module
    sys.path.insert(0, '.')
    from generate_benchmark_report import BenchmarkReportGenerator
    
    # Run report generation
    print(f"Generating HTML report at {report_path}...")
    report_generator = BenchmarkReportGenerator(
        data_file=json_path,
        summary_file=csv_path,
        visualizations_dir=viz_dir,
        output_file=report_path
    )
    report_generator.generate_html_report()
    
    return report_path

def main():
    """Main function to run the complete benchmark analysis pipeline."""
    # Parse command-line arguments
    args = parse_args()
    
    # Print banner
    print("\n" + "*"*80)
    print("*" + " "*78 + "*")
    print("*" + "  AEROSPIKE READ BENCHMARK ANALYSIS  ".center(78) + "*")
    print("*" + " "*78 + "*")
    print("*"*80 + "\n")
    
    # Print configuration
    print("Configuration:")
    print(f"  Data directory:       {args.data_dir}")
    print(f"  Output directory:     {args.output_dir}")
    print(f"  JSON file:            {args.json_file}")
    print(f"  CSV file:             {args.csv_file}")
    print(f"  Visualizations dir:   {args.viz_dir}")
    print(f"  HTML report file:     {args.report_file}")
    print(f"  Open report:          {args.open_report}")
    
    # Record start time
    start_time = datetime.now()
    
    # Run the pipeline
    try:
        # Step 1: Extract data
        json_path, csv_path = run_extraction(args)
        
        # Step 2: Generate visualizations
        viz_dir = run_visualization(args, json_path, csv_path)
        
        # Step 3: Generate HTML report
        report_path = run_report_generation(args, json_path, csv_path, viz_dir)
        
        # Calculate elapsed time
        elapsed_time = datetime.now() - start_time
        
        # Print success message
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"Elapsed time: {elapsed_time}")
        print(f"\nOutput files:")
        print(f"  JSON data:          {json_path}")
        print(f"  CSV summary:        {csv_path}")
        print(f"  Visualizations:     {viz_dir}")
        print(f"  HTML report:        {report_path}")
        
        # Open the report in the default browser if requested
        if args.open_report:
            print("\nOpening HTML report in default browser...")
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
