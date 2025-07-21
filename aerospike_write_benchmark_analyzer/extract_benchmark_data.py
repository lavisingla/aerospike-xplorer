#!/usr/bin/env python3
"""
Extract benchmark data from Aerospike write latency files.

This script parses HDR histogram files and write latency log files to extract
key metrics and store them in structured formats (JSON and CSV).
"""

import os
import re
import json
import csv
import argparse
from collections import defaultdict
import pandas as pd


def parse_hdr_file(file_path):
    """
    Parse an HDR histogram file and extract latency percentiles.
    
    Args:
        file_path: Path to the HDR histogram file
        
    Returns:
        dict: Dictionary containing latency percentiles and metadata
    """
    # Extract metadata from filename
    filename = os.path.basename(file_path)
    match = re.match(r'write_latency_(\d+)pct_(\d+)lastperc_(\d+)B_thr(\d+)\.txt', filename)
    if not match:
        raise ValueError(f"Invalid HDR filename format: {filename}")
    
    target_pct, last_pct, record_size, threads = match.groups()
    
    # Parse the HDR file content
    percentiles = {}
    mean = None
    std_dev = None
    max_value = None
    total_count = None
    db_size = None
    index_size = None
    
    with open(file_path, 'r') as f:
        # Skip the header line
        next(f)
        
        for line in f:
            line = line.strip()
            
            # Parse percentile data - match lines with latency values
            if line and not line.startswith('#') and not line.startswith('Database') and not line.startswith('INDEX'):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        value = float(parts[0])
                        percentile = float(parts[1])
                        percentiles[percentile] = value
                    except (ValueError, IndexError):
                        # Skip lines that don't have the expected format
                        continue
            
            # Parse summary statistics
            if line.startswith('#[Mean'):
                match = re.search(r'Mean\s+=\s+(\d+\.\d+)', line)
                if match:
                    mean = float(match.group(1))
                
                match = re.search(r'StdDeviation\s+=\s+(\d+\.\d+)', line)
                if match:
                    std_dev = float(match.group(1))
            
            if line.startswith('#[Max'):
                match = re.search(r'Max\s+=\s+(\d+\.\d+)', line)
                if match:
                    max_value = float(match.group(1))
                
                match = re.search(r'Total count\s+=\s+(\d+)', line)
                if match:
                    total_count = int(match.group(1))
            
            # Parse database size information
            if line.startswith('Database size:'):
                match = re.search(r'Total:\s+(\d+\.\d+)\s+MB', line)
                if match:
                    db_size = float(match.group(1))
            
            if line.startswith('INDEX size:'):
                match = re.search(r'Total:\s+(\d+\.\d+)\s+MB', line)
                if match:
                    index_size = float(match.group(1))
    
    # Extract key percentiles - find closest match if exact percentile not available
    def find_closest_percentile(target):
        if target in percentiles:
            return percentiles[target]
        
        # Find the closest percentile
        closest_percentile = None
        min_diff = float('inf')
        
        for p in percentiles.keys():
            diff = abs(p - target)
            if diff < min_diff:
                min_diff = diff
                closest_percentile = p
        
        # Only use if it's very close (within 0.001)
        if min_diff <= 0.001:
            return percentiles[closest_percentile]
        return None
    
    key_percentiles = {
        'p50': find_closest_percentile(0.5),
        'p90': find_closest_percentile(0.9),
        'p95': find_closest_percentile(0.95),
        'p99': find_closest_percentile(0.99),
        'p99.9': find_closest_percentile(0.999),
        'p99.99': find_closest_percentile(0.9999)
    }
    
    return {
        'metadata': {
            'target_pct': int(target_pct),
            'last_pct': int(last_pct),
            'record_size': int(record_size),
            'threads': int(threads),
            'db_size_mb': db_size,
            'index_size_mb': index_size
        },
        'statistics': {
            'mean': mean,
            'std_dev': std_dev,
            'max': max_value,
            'total_count': total_count
        },
        'percentiles': key_percentiles,
        'all_percentiles': percentiles
    }


def parse_log_file(file_path):
    """
    Parse a write latency log file and extract TPS and latency metrics over time.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        dict: Dictionary containing TPS and latency metrics over time
    """
    # Extract metadata from filename
    filename = os.path.basename(file_path)
    match = re.match(r'prefill_(\d+)pct_(\d+)B_(\d+)threads\.log', filename)
    if not match:
        raise ValueError(f"Invalid log filename format: {filename}")
    
    target_pct, record_size, threads = match.groups()
    
    # Determine the last_pct based on target_pct
    last_pct_mapping = {
        '25': 0,
        '50': 25,
        '75': 50
    }
    last_pct = last_pct_mapping.get(target_pct, 0)
    
    # Parse the log file content
    metrics = []
    config = {}
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Extract configuration information
            if ':' in line and not line.startswith('20') and not line.startswith('hdr:'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    config[key] = value
            
            # Extract HDR histogram data
            if line.startswith('hdr: write'):
                parts = line.split()
                if len(parts) >= 10:
                    timestamp = parts[2]
                    seconds = int(parts[3].rstrip(','))
                    total = int(parts[4].rstrip(','))
                    min_latency = int(parts[5].rstrip(','))
                    max_latency = int(parts[6].rstrip(','))
                    p50 = int(parts[7].rstrip(','))
                    p90 = int(parts[8].rstrip(','))
                    p99 = int(parts[9].rstrip(','))
                    p999 = int(parts[10].rstrip(','))
                    p9999 = int(parts[11]) if len(parts) > 11 else None
                    
                    metrics.append({
                        'timestamp': timestamp,
                        'seconds': seconds,
                        'total': total,
                        'min_latency': min_latency,
                        'max_latency': max_latency,
                        'p50': p50,
                        'p90': p90,
                        'p99': p99,
                        'p999': p999,
                        'p9999': p9999
                    })
            
            # Extract TPS information
            if 'write(tps=' in line:
                match = re.search(r'write\(tps=(\d+)', line)
                if match and metrics:  # Add to the last metrics entry
                    tps = int(match.group(1))
                    metrics[-1]['tps'] = tps
    
    return {
        'metadata': {
            'target_pct': int(target_pct),
            'last_pct': last_pct,
            'record_size': int(record_size),
            'threads': int(threads)
        },
        'config': config,
        'metrics': metrics
    }


def extract_benchmark_data(data_dir, output_dir, json_file, csv_file):
    """
    Extract benchmark data from HDR histogram files and log files.
    
    Args:
        data_dir: Directory containing benchmark data
        output_dir: Directory for output files
        json_file: Output JSON file name
        csv_file: Output CSV file name
    
    Returns:
        dict: Dictionary containing all benchmark data
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all HDR histogram files and log files
    hdr_dir = os.path.join(data_dir, 'hdr_stats')
    log_dir = os.path.join(data_dir, 'write_latency_results')
    
    hdr_files = []
    if os.path.exists(hdr_dir):
        hdr_files = [os.path.join(hdr_dir, f) for f in os.listdir(hdr_dir) if f.endswith('.txt')]
    
    log_files = []
    if os.path.exists(log_dir):
        log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
    
    # Parse all files
    hdr_data = {}
    log_data = {}
    
    print(f"Processing {len(hdr_files)} HDR histogram files...")
    for file_path in hdr_files:
        try:
            data = parse_hdr_file(file_path)
            filename = os.path.basename(file_path)
            hdr_data[filename] = data
            print(f"Processed {filename}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f"\nProcessing {len(log_files)} log files...")
    for file_path in log_files:
        try:
            data = parse_log_file(file_path)
            filename = os.path.basename(file_path)
            log_data[filename] = data
            print(f"Processed {filename}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Combine data
    benchmark_data = {
        'hdr_data': hdr_data,
        'log_data': log_data
    }
    
    # Save data to JSON
    json_path = os.path.join(output_dir, json_file)
    with open(json_path, 'w') as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"\nSaved benchmark data to {json_path}")
    
    # Create summary CSV
    csv_path = os.path.join(output_dir, csv_file)
    create_summary_csv(benchmark_data, csv_path)
    print(f"Saved benchmark summary to {csv_path}")
    
    return benchmark_data


def create_summary_csv(benchmark_data, csv_path):
    """
    Create a summary CSV file from benchmark data.
    
    Args:
        benchmark_data: Dictionary containing benchmark data
        csv_path: Path to output CSV file
    """
    summary_data = []
    
    # Define all possible fields to ensure consistency
    all_fields = [
        'source', 'filename', 'target_pct', 'last_pct', 'record_size', 'threads',
        'mean_latency', 'max_latency', 'p50', 'p90', 'p95', 'p99', 'p99.9', 'p99.99',
        'db_size_mb', 'index_size_mb', 'tps'
    ]
    
    # Process HDR data
    for filename, data in benchmark_data['hdr_data'].items():
        metadata = data['metadata']
        percentiles = data['percentiles']
        statistics = data['statistics']
        
        row = {
            'source': 'hdr',
            'filename': filename,
            'target_pct': metadata['target_pct'],
            'last_pct': metadata['last_pct'],
            'record_size': metadata['record_size'],
            'threads': metadata['threads'],
            'mean_latency': statistics['mean'],
            'max_latency': statistics['max'],
            'p50': percentiles['p50'],
            'p90': percentiles['p90'],
            'p95': percentiles['p95'],
            'p99': percentiles['p99'],
            'p99.9': percentiles['p99.9'],
            'p99.99': percentiles['p99.99'],
            'db_size_mb': metadata['db_size_mb'],
            'index_size_mb': metadata['index_size_mb'],
            'tps': None  # Add tps field with None value for HDR data
        }
        summary_data.append(row)
    
    # Process log data - calculate averages
    for filename, data in benchmark_data['log_data'].items():
        metadata = data['metadata']
        metrics = data['metrics']
        
        if not metrics:
            continue
        
        # Calculate averages
        avg_tps = sum(m.get('tps', 0) for m in metrics) / len(metrics)
        avg_p50 = sum(m.get('p50', 0) for m in metrics) / len(metrics)
        avg_p90 = sum(m.get('p90', 0) for m in metrics) / len(metrics)
        avg_p99 = sum(m.get('p99', 0) for m in metrics) / len(metrics)
        avg_p999 = sum(m.get('p999', 0) for m in metrics) / len(metrics)
        avg_p9999 = sum(m.get('p9999', 0) for m in metrics if m.get('p9999') is not None) / len([m for m in metrics if m.get('p9999') is not None]) if any(m.get('p9999') is not None for m in metrics) else None
        
        row = {
            'source': 'log',
            'filename': filename,
            'target_pct': metadata['target_pct'],
            'last_pct': metadata['last_pct'],
            'record_size': metadata['record_size'],
            'threads': metadata['threads'],
            'mean_latency': None,  # Add fields that exist in HDR data but not in log data
            'max_latency': None,
            'p50': avg_p50,
            'p90': avg_p90,
            'p95': None,  # p95 not available in log data
            'p99': avg_p99,
            'p99.9': avg_p999,
            'p99.99': avg_p9999,
            'db_size_mb': None,
            'index_size_mb': None,
            'tps': avg_tps
        }
        summary_data.append(row)
    
    # Write to CSV
    if summary_data:
        with open(csv_path, 'w', newline='') as f:
            dict_writer = csv.DictWriter(f, fieldnames=all_fields)
            dict_writer.writeheader()
            dict_writer.writerows(summary_data)


def main():
    """Main function to extract benchmark data."""
    parser = argparse.ArgumentParser(description='Extract Aerospike write benchmark data')
    parser.add_argument('--data-dir', default='.', help='Directory containing benchmark data')
    parser.add_argument('--output-dir', default='benchmark_analysis', help='Directory for output files')
    parser.add_argument('--json-file', default='benchmark_data.json', help='Output JSON file name')
    parser.add_argument('--csv-file', default='benchmark_summary.csv', help='Output CSV file name')
    args = parser.parse_args()
    
    extract_benchmark_data(args.data_dir, args.output_dir, args.json_file, args.csv_file)


if __name__ == '__main__':
    main()
