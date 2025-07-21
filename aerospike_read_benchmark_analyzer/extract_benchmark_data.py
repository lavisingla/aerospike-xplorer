#!/usr/bin/env python3
"""
Aerospike Read Benchmark Data Extraction Script

This script extracts key metrics from Aerospike read benchmark data:
- HDR histogram files (latency distributions)
- Read latency log files (performance metrics)

The extracted data is saved in structured formats (CSV/JSON) for further analysis.
"""

import os
import re
import json
import csv
import glob
from collections import defaultdict
import pandas as pd

class BenchmarkDataExtractor:
    def __init__(self, base_dir='.'):
        """Initialize the extractor with the base directory containing benchmark data."""
        self.base_dir = base_dir
        self.hdr_stats_dir = os.path.join(base_dir, 'hdr_stats')
        self.latency_results_dir = os.path.join(base_dir, 'read_latency_results')
        
        # Regular expressions for parsing file names
        self.file_pattern = re.compile(r'read_latency_(\d+)pct_(\d+)B_thr(\d+)_(\d+)')
        
        # Data structures to store extracted data
        self.hdr_data = {}  # Will store HDR histogram data
        self.log_data = {}  # Will store log file data
        
    def parse_filename(self, filename):
        """Parse benchmark parameters from filename."""
        match = self.file_pattern.search(filename)
        if match:
            pct, size, threads, timestamp = match.groups()
            return {
                'percentage': int(pct),
                'size_bytes': int(size),
                'threads': int(threads),
                'timestamp': timestamp
            }
        return None
    
    def extract_hdr_stats(self):
        """Extract data from HDR histogram files."""
        hdr_files = glob.glob(os.path.join(self.hdr_stats_dir, '*.txt'))
        
        for hdr_file in hdr_files:
            filename = os.path.basename(hdr_file)
            params = self.parse_filename(filename)
            
            if not params:
                continue
                
            key = (params['percentage'], params['size_bytes'], params['threads'])
            
            with open(hdr_file, 'r') as f:
                content = f.read()
                
                # Extract percentile data
                percentile_data = []
                for line in content.split('\n'):
                    if line and not line.startswith('#') and not line.startswith('Database'):
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            try:
                                value = float(parts[0])
                                percentile = float(parts[1])
                                count = int(parts[2])
                                percentile_data.append({
                                    'value_us': value,
                                    'percentile': percentile,
                                    'count': count
                                })
                            except (ValueError, IndexError):
                                continue
                
                # Extract summary statistics
                summary = {}
                for line in content.split('\n'):
                    if line.startswith('#[Mean'):
                        match = re.search(r'Mean\s+=\s+([0-9.]+),\s+StdDeviation\s+=\s+([0-9.]+)', line)
                        if match:
                            summary['mean'] = float(match.group(1))
                            summary['std_dev'] = float(match.group(2))
                    elif line.startswith('#[Max'):
                        match = re.search(r'Max\s+=\s+([0-9.]+),\s+Total count\s+=\s+([0-9]+)', line)
                        if match:
                            summary['max'] = float(match.group(1))
                            summary['total_count'] = int(match.group(2))
                    elif line.startswith('Database size:'):
                        match = re.search(r'Database size: Total: ([0-9.]+) MB', line)
                        if match:
                            summary['db_size_mb'] = float(match.group(1))
                    elif line.startswith('INDEX size:'):
                        match = re.search(r'INDEX size: Total: ([0-9.]+) MB', line)
                        if match:
                            summary['index_size_mb'] = float(match.group(1))
                
                # Store the extracted data
                self.hdr_data[key] = {
                    'params': params,
                    'percentile_data': percentile_data,
                    'summary': summary
                }
        
        return self.hdr_data
    
    def extract_log_data(self):
        """Extract data from read latency log files."""
        log_files = glob.glob(os.path.join(self.latency_results_dir, 'read_latency_*.log'))
        
        for log_file in log_files:
            filename = os.path.basename(log_file)
            params = self.parse_filename(filename)
            
            if not params:
                continue
                
            key = (params['percentage'], params['size_bytes'], params['threads'])
            
            config = {}
            per_second_data = []
            
            with open(log_file, 'r') as f:
                in_config = True
                
                for line in f:
                    line = line.strip()
                    
                    # Parse configuration section
                    if in_config and ':' in line and not line.startswith('2025-'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            config[parts[0].strip()] = parts[1].strip()
                    
                    # Detect end of configuration section
                    if line.startswith('Stage 1:'):
                        in_config = False
                        continue
                    
                    # Parse per-second performance data
                    if line.startswith('2025-') and 'read(tps=' in line:
                        timestamp = line.split()[0] + ' ' + line.split()[1]
                        
                        # Extract TPS data
                        tps_match = re.search(r'read\(tps=(\d+) \(hit=(\d+) miss=(\d+)\) timeouts=(\d+) errors=(\d+)\)', line)
                        if tps_match:
                            tps, hits, misses, timeouts, errors = map(int, tps_match.groups())
                            
                            second_data = {
                                'timestamp': timestamp,
                                'tps': tps,
                                'hits': hits,
                                'misses': misses,
                                'timeouts': timeouts,
                                'errors': errors
                            }
                            
                            per_second_data.append(second_data)
                    
                    # Parse HDR histogram line
                    if line.startswith('hdr: read'):
                        parts = line.split()
                        if len(parts) >= 10:
                            try:
                                hdr_data = {
                                    'timestamp': parts[2],
                                    'seconds': int(parts[3].rstrip(',')),
                                    'total': int(parts[4].rstrip(',')),
                                    'min_latency': int(parts[5].rstrip(',')),
                                    'max_latency': int(parts[6].rstrip(',')),
                                    'p50': int(parts[7].rstrip(',')),
                                    'p90': int(parts[8].rstrip(',')),
                                    'p99': int(parts[9].rstrip(',')),
                                    'p99_9': int(parts[10].rstrip(',')),
                                    'p99_99': int(parts[11]) if len(parts) > 11 else None
                                }
                                
                                # Add HDR data to the last second_data entry
                                if per_second_data:
                                    per_second_data[-1].update(hdr_data)
                            except (ValueError, IndexError):
                                continue
            
            # Calculate aggregate statistics
            if per_second_data:
                tps_values = [entry['tps'] for entry in per_second_data]
                avg_tps = sum(tps_values) / len(tps_values)
                max_tps = max(tps_values)
                min_tps = min(tps_values)
                
                # Calculate latency statistics (excluding warmup period - first 10 seconds)
                stable_data = per_second_data[10:] if len(per_second_data) > 10 else per_second_data
                
                p50_values = [entry.get('p50', 0) for entry in stable_data if 'p50' in entry]
                p90_values = [entry.get('p90', 0) for entry in stable_data if 'p90' in entry]
                p99_values = [entry.get('p99', 0) for entry in stable_data if 'p99' in entry]
                
                latency_stats = {
                    'avg_p50': sum(p50_values) / len(p50_values) if p50_values else 0,
                    'avg_p90': sum(p90_values) / len(p90_values) if p90_values else 0,
                    'avg_p99': sum(p99_values) / len(p99_values) if p99_values else 0,
                    'min_p50': min(p50_values) if p50_values else 0,
                    'min_p90': min(p90_values) if p90_values else 0,
                    'min_p99': min(p99_values) if p99_values else 0,
                    'max_p50': max(p50_values) if p50_values else 0,
                    'max_p90': max(p90_values) if p90_values else 0,
                    'max_p99': max(p99_values) if p99_values else 0
                }
                
                # Store the extracted data
                self.log_data[key] = {
                    'params': params,
                    'config': config,
                    'per_second_data': per_second_data,
                    'aggregate': {
                        'avg_tps': avg_tps,
                        'max_tps': max_tps,
                        'min_tps': min_tps,
                        'latency': latency_stats
                    }
                }
        
        return self.log_data
    
    def extract_all_data(self):
        """Extract all benchmark data."""
        self.extract_hdr_stats()
        self.extract_log_data()
        return {
            'hdr_data': self.hdr_data,
            'log_data': self.log_data
        }
    
    def save_to_json(self, output_file='benchmark_data.json'):
        """Save extracted data to JSON file."""
        data = self.extract_all_data()
        
        # Convert keys from tuples to strings for JSON serialization
        serializable_data = {
            'hdr_data': {f"{k[0]}pct_{k[1]}B_thr{k[2]}": v for k, v in data['hdr_data'].items()},
            'log_data': {f"{k[0]}pct_{k[1]}B_thr{k[2]}": v for k, v in data['log_data'].items()}
        }
        
        with open(output_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        
        return output_file
    
    def save_summary_to_csv(self, output_file='benchmark_summary.csv'):
        """Save summary of benchmark results to CSV file."""
        if not self.hdr_data or not self.log_data:
            self.extract_all_data()
        
        # Prepare data for CSV
        rows = []
        
        for key in sorted(self.log_data.keys()):
            pct, size_bytes, threads = key
            
            log_entry = self.log_data.get(key, {})
            hdr_entry = self.hdr_data.get(key, {})
            
            if not log_entry or not hdr_entry:
                continue
            
            # Get aggregate statistics
            agg = log_entry.get('aggregate', {})
            latency = agg.get('latency', {})
            summary = hdr_entry.get('summary', {})
            
            row = {
                'percentage': pct,
                'size_kb': size_bytes / 1024,
                'threads': threads,
                'avg_tps': round(agg.get('avg_tps', 0), 2),
                'max_tps': agg.get('max_tps', 0),
                'min_tps': agg.get('min_tps', 0),
                'avg_p50_us': round(latency.get('avg_p50', 0), 2),
                'avg_p90_us': round(latency.get('avg_p90', 0), 2),
                'avg_p99_us': round(latency.get('avg_p99', 0), 2),
                'max_p99_us': latency.get('max_p99', 0),
                'mean_latency_us': round(summary.get('mean', 0), 2),
                'max_latency_us': summary.get('max', 0),
                'std_dev_us': round(summary.get('std_dev', 0), 2),
                'db_size_mb': summary.get('db_size_mb', 0),
                'index_size_mb': summary.get('index_size_mb', 0)
            }
            
            rows.append(row)
        
        # Write to CSV
        if rows:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        return output_file
    
    def create_dataframes(self):
        """Create pandas DataFrames from the extracted data for easier analysis."""
        if not self.hdr_data or not self.log_data:
            self.extract_all_data()
        
        # Create summary DataFrame
        summary_rows = []
        
        for key in sorted(self.log_data.keys()):
            pct, size_bytes, threads = key
            
            log_entry = self.log_data.get(key, {})
            hdr_entry = self.hdr_data.get(key, {})
            
            if not log_entry or not hdr_entry:
                continue
            
            # Get aggregate statistics
            agg = log_entry.get('aggregate', {})
            latency = agg.get('latency', {})
            summary = hdr_entry.get('summary', {})
            
            row = {
                'percentage': pct,
                'size_kb': size_bytes / 1024,
                'threads': threads,
                'avg_tps': agg.get('avg_tps', 0),
                'max_tps': agg.get('max_tps', 0),
                'min_tps': agg.get('min_tps', 0),
                'avg_p50_us': latency.get('avg_p50', 0),
                'avg_p90_us': latency.get('avg_p90', 0),
                'avg_p99_us': latency.get('avg_p99', 0),
                'max_p99_us': latency.get('max_p99', 0),
                'mean_latency_us': summary.get('mean', 0),
                'max_latency_us': summary.get('max', 0),
                'std_dev_us': summary.get('std_dev', 0),
                'db_size_mb': summary.get('db_size_mb', 0),
                'index_size_mb': summary.get('index_size_mb', 0)
            }
            
            summary_rows.append(row)
        
        summary_df = pd.DataFrame(summary_rows)
        
        # Create per-second DataFrame
        per_second_rows = []
        
        for key, log_entry in self.log_data.items():
            pct, size_bytes, threads = key
            
            for second_data in log_entry.get('per_second_data', []):
                row = {
                    'percentage': pct,
                    'size_kb': size_bytes / 1024,
                    'threads': threads,
                    'timestamp': second_data.get('timestamp'),
                    'seconds': second_data.get('seconds', 0),
                    'tps': second_data.get('tps', 0),
                    'hits': second_data.get('hits', 0),
                    'misses': second_data.get('misses', 0),
                    'timeouts': second_data.get('timeouts', 0),
                    'errors': second_data.get('errors', 0),
                    'p50': second_data.get('p50', 0),
                    'p90': second_data.get('p90', 0),
                    'p99': second_data.get('p99', 0),
                    'p99_9': second_data.get('p99_9', 0),
                    'p99_99': second_data.get('p99_99', 0)
                }
                
                per_second_rows.append(row)
        
        per_second_df = pd.DataFrame(per_second_rows)
        
        return {
            'summary': summary_df,
            'per_second': per_second_df
        }

def main():
    """Main function to extract and save benchmark data."""
    extractor = BenchmarkDataExtractor()
    
    # Extract and save data
    json_file = extractor.save_to_json()
    csv_file = extractor.save_summary_to_csv()
    
    print(f"Benchmark data extracted and saved to {json_file} and {csv_file}")
    
    # Create DataFrames for further analysis
    dataframes = extractor.create_dataframes()
    
    # Print some basic statistics
    summary_df = dataframes['summary']
    print("\nBenchmark Summary Statistics:")
    print(f"Total configurations tested: {len(summary_df)}")
    print(f"Average TPS across all tests: {summary_df['avg_tps'].mean():.2f}")
    print(f"Maximum TPS achieved: {summary_df['max_tps'].max()} (configuration: {summary_df.loc[summary_df['max_tps'].idxmax()][['percentage', 'size_kb', 'threads']].to_dict()})")
    print(f"Minimum p99 latency: {summary_df['avg_p99_us'].min():.2f} μs (configuration: {summary_df.loc[summary_df['avg_p99_us'].idxmin()][['percentage', 'size_kb', 'threads']].to_dict()})")

if __name__ == "__main__":
    main()
