#!/usr/bin/env python3
"""
Visualize benchmark data from Aerospike write latency files.

This script generates various visualizations from the extracted benchmark data.
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter


def load_benchmark_data(json_path):
    """
    Load benchmark data from JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        dict: Dictionary containing benchmark data
    """
    with open(json_path, 'r') as f:
        return json.load(f)


def create_dataframes(benchmark_data):
    """
    Create pandas DataFrames from benchmark data.
    
    Args:
        benchmark_data: Dictionary containing benchmark data
        
    Returns:
        tuple: (hdr_df, log_df) DataFrames
    """
    # Create HDR DataFrame
    hdr_rows = []
    for filename, data in benchmark_data['hdr_data'].items():
        metadata = data['metadata']
        percentiles = data['percentiles']
        statistics = data['statistics']
        
        row = {
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
            'index_size_mb': metadata['index_size_mb']
        }
        hdr_rows.append(row)
    
    hdr_df = pd.DataFrame(hdr_rows)
    
    # Create log DataFrame
    log_rows = []
    for filename, data in benchmark_data['log_data'].items():
        metadata = data['metadata']
        metrics = data['metrics']
        
        for metric in metrics:
            row = {
                'filename': filename,
                'target_pct': metadata['target_pct'],
                'last_pct': metadata['last_pct'],
                'record_size': metadata['record_size'],
                'threads': metadata['threads'],
                'timestamp': metric.get('timestamp'),
                'seconds': metric.get('seconds'),
                'total': metric.get('total'),
                'min_latency': metric.get('min_latency'),
                'max_latency': metric.get('max_latency'),
                'p50': metric.get('p50'),
                'p90': metric.get('p90'),
                'p99': metric.get('p99'),
                'p99.9': metric.get('p999'),
                'p99.99': metric.get('p9999'),
                'tps': metric.get('tps')
            }
            log_rows.append(row)
    
    log_df = pd.DataFrame(log_rows)
    
    return hdr_df, log_df


def setup_visualization_dir(output_dir):
    """
    Set up the visualization directory.
    
    Args:
        output_dir: Directory for output files
        
    Returns:
        str: Path to the visualization directory
    """
    viz_dir = os.path.join(output_dir, 'visualizations')
    os.makedirs(viz_dir, exist_ok=True)
    return viz_dir


def set_plot_style():
    """Set the plot style for visualizations."""
    plt.style.use('ggplot')
    sns.set(style="whitegrid")
    sns.set_palette("colorblind")
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 12


def format_latency(x, pos):
    """Format latency values for axis labels."""
    if x >= 1000000:
        return f'{x/1000000:.1f}s'
    elif x >= 1000:
        return f'{x/1000:.1f}ms'
    else:
        return f'{x:.0f}μs'


def plot_latency_percentiles_by_thread_count(hdr_df, viz_dir):
    """
    Plot latency percentiles by thread count.
    
    Args:
        hdr_df: DataFrame containing HDR data
        viz_dir: Directory for output visualizations
    """
    percentiles = ['p50', 'p90', 'p99', 'p99.9', 'p99.99']
    record_sizes = sorted(hdr_df['record_size'].unique())
    target_pcts = sorted(hdr_df['target_pct'].unique())
    
    for record_size in record_sizes:
        for target_pct in target_pcts:
            df_subset = hdr_df[(hdr_df['record_size'] == record_size) & 
                              (hdr_df['target_pct'] == target_pct)]
            
            if df_subset.empty:
                continue
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            for percentile in percentiles:
                df_subset_sorted = df_subset.sort_values('threads')
                ax.plot(df_subset_sorted['threads'], df_subset_sorted[percentile], 
                        marker='o', linewidth=2, label=percentile)
            
            ax.set_xlabel('Thread Count')
            ax.set_ylabel('Latency (μs)')
            ax.set_title(f'Write Latency Percentiles by Thread Count\n'
                        f'Record Size: {record_size}B, Target Fill: {target_pct}%')
            ax.legend()
            ax.grid(True)
            ax.yaxis.set_major_formatter(FuncFormatter(format_latency))
            
            # Save the figure
            filename = f'latency_percentiles_by_thread_count_{record_size}B_{target_pct}pct.png'
            plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()


def plot_tps_by_thread_count(log_df, viz_dir):
    """
    Plot TPS by thread count.
    
    Args:
        log_df: DataFrame containing log data
        viz_dir: Directory for output visualizations
    """
    record_sizes = sorted(log_df['record_size'].unique())
    target_pcts = sorted(log_df['target_pct'].unique())
    
    # Calculate average TPS for each configuration
    tps_avg = log_df.groupby(['record_size', 'target_pct', 'threads'])['tps'].mean().reset_index()
    
    for record_size in record_sizes:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for target_pct in target_pcts:
            df_subset = tps_avg[(tps_avg['record_size'] == record_size) & 
                               (tps_avg['target_pct'] == target_pct)]
            
            if df_subset.empty:
                continue
            
            df_subset_sorted = df_subset.sort_values('threads')
            ax.plot(df_subset_sorted['threads'], df_subset_sorted['tps'], 
                    marker='o', linewidth=2, label=f'Fill {target_pct}%')
        
        ax.set_xlabel('Thread Count')
        ax.set_ylabel('Transactions Per Second (TPS)')
        ax.set_title(f'Write TPS by Thread Count\nRecord Size: {record_size}B')
        ax.legend()
        ax.grid(True)
        
        # Save the figure
        filename = f'tps_by_thread_count_{record_size}B.png'
        plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()


def plot_latency_by_record_size(hdr_df, viz_dir):
    """
    Plot latency by record size.
    
    Args:
        hdr_df: DataFrame containing HDR data
        viz_dir: Directory for output visualizations
    """
    percentiles = ['p50', 'p99', 'p99.9']
    thread_counts = sorted(hdr_df['threads'].unique())
    target_pcts = sorted(hdr_df['target_pct'].unique())
    
    for thread_count in thread_counts:
        for percentile in percentiles:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            for target_pct in target_pcts:
                df_subset = hdr_df[(hdr_df['threads'] == thread_count) & 
                                  (hdr_df['target_pct'] == target_pct)]
                
                if df_subset.empty:
                    continue
                
                df_subset_sorted = df_subset.sort_values('record_size')
                ax.plot(df_subset_sorted['record_size'], df_subset_sorted[percentile], 
                        marker='o', linewidth=2, label=f'Fill {target_pct}%')
            
            ax.set_xlabel('Record Size (bytes)')
            ax.set_ylabel(f'{percentile} Latency (μs)')
            ax.set_title(f'Write {percentile} Latency by Record Size\nThread Count: {thread_count}')
            ax.legend()
            ax.grid(True)
            ax.set_xscale('log', base=2)
            ax.yaxis.set_major_formatter(FuncFormatter(format_latency))
            
            # Save the figure
            filename = f'latency_by_record_size_{percentile}_thr{thread_count}.png'
            plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()


def plot_latency_heatmap(hdr_df, viz_dir):
    """
    Plot latency heatmap.
    
    Args:
        hdr_df: DataFrame containing HDR data
        viz_dir: Directory for output visualizations
    """
    percentiles = ['p50', 'p99', 'p99.9']
    target_pcts = sorted(hdr_df['target_pct'].unique())
    
    for percentile in percentiles:
        for target_pct in target_pcts:
            # Print the data to debug
            print(f"\nCreating heatmap for {percentile} at {target_pct}% fill")
            print(f"Available data points: {len(hdr_df[hdr_df['target_pct'] == target_pct])}")
            
            # Create a pivot table directly without filtering first
            pivot_data = hdr_df[hdr_df['target_pct'] == target_pct].pivot_table(
                index='record_size', 
                columns='threads',
                values=percentile,
                aggfunc='mean'
            )
            
            # Check if pivot table is empty or has only NaN values
            if pivot_data.empty or pivot_data.isnull().all().all():
                print(f"Skipping empty heatmap for {percentile} at {target_pct}% fill")
                
                # Debug: Print the unique values to understand what's available
                print(f"Unique record sizes: {hdr_df['record_size'].unique()}")
                print(f"Unique thread counts: {hdr_df['threads'].unique()}")
                print(f"Sample of {percentile} values: {hdr_df[percentile].head()}")
                continue
            
            # Sort the indices
            pivot_data = pivot_data.sort_index()
            
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
            
            ax.set_title(f'Write {percentile} Latency Heatmap\nTarget Fill: {target_pct}%')
            ax.set_xlabel('Thread Count')
            ax.set_ylabel('Record Size (bytes)')
            
            # Save the figure
            filename = f'latency_heatmap_{percentile}_{target_pct}pct.png'
            plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()


def plot_tps_heatmap(log_df, viz_dir):
    """
    Plot TPS heatmap.
    
    Args:
        log_df: DataFrame containing log data
        viz_dir: Directory for output visualizations
    """
    target_pcts = sorted(log_df['target_pct'].unique())
    
    # Calculate average TPS for each configuration
    tps_avg = log_df.groupby(['record_size', 'target_pct', 'threads'])['tps'].mean().reset_index()
    
    for target_pct in target_pcts:
        df_subset = tps_avg[tps_avg['target_pct'] == target_pct]
        
        if df_subset.empty:
            continue
        
        # Create a pivot table for the heatmap
        pivot_data = df_subset.pivot_table(
            index='record_size', 
            columns='threads',
            values='tps',
            aggfunc='mean'
        )
        
        # Check if pivot table is empty or has only NaN values
        if pivot_data.empty or pivot_data.isnull().all().all():
            print(f"Skipping empty TPS heatmap for {target_pct}% fill")
            continue
        
        # Sort the indices
        pivot_data = pivot_data.sort_index()
        
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='viridis', ax=ax)
        
        ax.set_title(f'Write TPS Heatmap\nTarget Fill: {target_pct}%')
        ax.set_xlabel('Thread Count')
        ax.set_ylabel('Record Size (bytes)')
        
        # Save the figure
        filename = f'tps_heatmap_{target_pct}pct.png'
        plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()


def plot_latency_distribution(hdr_df, benchmark_data, viz_dir):
    """
    Plot latency distribution curves.
    
    Args:
        hdr_df: DataFrame containing HDR data
        benchmark_data: Dictionary containing benchmark data
        viz_dir: Directory for output visualizations
    """
    record_sizes = sorted(hdr_df['record_size'].unique())
    thread_counts = sorted(hdr_df['threads'].unique())
    target_pcts = sorted(hdr_df['target_pct'].unique())
    
    for record_size in record_sizes:
        for thread_count in thread_counts:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            for target_pct in target_pcts:
                # Find the corresponding file
                for filename, data in benchmark_data['hdr_data'].items():
                    metadata = data['metadata']
                    if (metadata['record_size'] == record_size and 
                        metadata['threads'] == thread_count and 
                        metadata['target_pct'] == target_pct):
                        
                        # Extract percentiles for plotting
                        percentiles = []
                        latencies = []
                        for p, latency in data['all_percentiles'].items():
                            if float(p) > 0 and float(p) < 1:  # Skip 0 and 1
                                percentiles.append(float(p))
                                latencies.append(latency)
                        
                        # Sort by percentile
                        sorted_data = sorted(zip(percentiles, latencies))
                        percentiles = [p for p, _ in sorted_data]
                        latencies = [l for _, l in sorted_data]
                        
                        # Plot
                        ax.plot(percentiles, latencies, linewidth=2, 
                                label=f'Fill {target_pct}%')
                        break
            
            ax.set_xlabel('Percentile')
            ax.set_ylabel('Latency (μs)')
            ax.set_title(f'Write Latency Distribution\n'
                        f'Record Size: {record_size}B, Thread Count: {thread_count}')
            ax.legend()
            ax.grid(True)
            ax.set_xscale('logit')
            ax.set_xlim(0.01, 0.999)
            ax.yaxis.set_major_formatter(FuncFormatter(format_latency))
            
            # Save the figure
            filename = f'latency_distribution_{record_size}B_thr{thread_count}.png'
            plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()


def plot_tps_over_time(log_df, viz_dir):
    """
    Plot TPS over time.
    
    Args:
        log_df: DataFrame containing log data
        viz_dir: Directory for output visualizations
    """
    record_sizes = sorted(log_df['record_size'].unique())
    thread_counts = sorted(log_df['threads'].unique())
    target_pcts = sorted(log_df['target_pct'].unique())
    
    for record_size in record_sizes:
        for thread_count in thread_counts:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            for target_pct in target_pcts:
                df_subset = log_df[(log_df['record_size'] == record_size) & 
                                  (log_df['threads'] == thread_count) & 
                                  (log_df['target_pct'] == target_pct)]
                
                if df_subset.empty:
                    continue
                
                df_subset_sorted = df_subset.sort_values('seconds')
                ax.plot(df_subset_sorted['seconds'], df_subset_sorted['tps'], 
                        linewidth=2, label=f'Fill {target_pct}%')
            
            ax.set_xlabel('Time (seconds)')
            ax.set_ylabel('Transactions Per Second (TPS)')
            ax.set_title(f'Write TPS Over Time\n'
                        f'Record Size: {record_size}B, Thread Count: {thread_count}')
            ax.legend()
            ax.grid(True)
            
            # Save the figure
            filename = f'tps_over_time_{record_size}B_thr{thread_count}.png'
            plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()


def plot_latency_over_time(log_df, viz_dir):
    """
    Plot latency over time.
    
    Args:
        log_df: DataFrame containing log data
        viz_dir: Directory for output visualizations
    """
    percentiles = ['p50', 'p99', 'p99.9']
    record_sizes = sorted(log_df['record_size'].unique())
    thread_counts = sorted(log_df['threads'].unique())
    target_pcts = sorted(log_df['target_pct'].unique())
    
    for record_size in record_sizes:
        for thread_count in thread_counts:
            for percentile in percentiles:
                fig, ax = plt.subplots(figsize=(12, 8))
                
                for target_pct in target_pcts:
                    df_subset = log_df[(log_df['record_size'] == record_size) & 
                                      (log_df['threads'] == thread_count) & 
                                      (log_df['target_pct'] == target_pct)]
                    
                    if df_subset.empty:
                        continue
                    
                    df_subset_sorted = df_subset.sort_values('seconds')
                    ax.plot(df_subset_sorted['seconds'], df_subset_sorted[percentile], 
                            linewidth=2, label=f'Fill {target_pct}%')
                
                ax.set_xlabel('Time (seconds)')
                ax.set_ylabel(f'{percentile} Latency (μs)')
                ax.set_title(f'Write {percentile} Latency Over Time\n'
                            f'Record Size: {record_size}B, Thread Count: {thread_count}')
                ax.legend()
                ax.grid(True)
                ax.yaxis.set_major_formatter(FuncFormatter(format_latency))
                
                # Save the figure
                filename = f'latency_over_time_{percentile}_{record_size}B_thr{thread_count}.png'
                plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
                plt.close()


def plot_fill_level_impact(hdr_df, viz_dir):
    """
    Plot impact of fill level on latency.
    
    Args:
        hdr_df: DataFrame containing HDR data
        viz_dir: Directory for output visualizations
    """
    percentiles = ['p50', 'p99', 'p99.9']
    record_sizes = sorted(hdr_df['record_size'].unique())
    thread_counts = sorted(hdr_df['threads'].unique())
    
    for record_size in record_sizes:
        for percentile in percentiles:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            for thread_count in thread_counts:
                df_subset = hdr_df[(hdr_df['record_size'] == record_size) & 
                                  (hdr_df['threads'] == thread_count)]
                
                if df_subset.empty:
                    continue
                
                df_subset_sorted = df_subset.sort_values('target_pct')
                ax.plot(df_subset_sorted['target_pct'], df_subset_sorted[percentile], 
                        marker='o', linewidth=2, label=f'{thread_count} Threads')
            
            ax.set_xlabel('Target Fill Level (%)')
            ax.set_ylabel(f'{percentile} Latency (μs)')
            ax.set_title(f'Impact of Fill Level on Write {percentile} Latency\n'
                        f'Record Size: {record_size}B')
            ax.legend()
            ax.grid(True)
            ax.yaxis.set_major_formatter(FuncFormatter(format_latency))
            
            # Save the figure
            filename = f'fill_level_impact_{percentile}_{record_size}B.png'
            plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()


def plot_comparative_analysis(hdr_df, log_df, viz_dir):
    """
    Plot comparative analysis charts.
    
    Args:
        hdr_df: DataFrame containing HDR data
        log_df: DataFrame containing log data
        viz_dir: Directory for output visualizations
    """
    # Calculate average TPS for each configuration
    tps_avg = log_df.groupby(['record_size', 'target_pct', 'threads'])['tps'].mean().reset_index()
    
    # Merge with HDR data
    merged_df = pd.merge(
        hdr_df,
        tps_avg,
        on=['record_size', 'target_pct', 'threads'],
        how='inner'
    )
    
    # Remove rows with None values in critical columns
    merged_df = merged_df.dropna(subset=['tps', 'p99'])
    
    if merged_df.empty:
        print("Skipping comparative analysis charts due to insufficient data")
        return
    
    # Plot TPS vs p99 latency
    record_sizes = sorted(merged_df['record_size'].unique())
    target_pcts = sorted(merged_df['target_pct'].unique())
    
    for record_size in record_sizes:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for target_pct in target_pcts:
            df_subset = merged_df[(merged_df['record_size'] == record_size) & 
                                (merged_df['target_pct'] == target_pct)]
            
            if df_subset.empty:
                continue
            
            ax.scatter(df_subset['tps'], df_subset['p99'], 
                      s=100, alpha=0.7, label=f'Fill {target_pct}%')
            
            # Add thread count annotations
            for _, row in df_subset.iterrows():
                # Ensure we have valid values for annotation
                if pd.notna(row['tps']) and pd.notna(row['p99']):
                    ax.annotate(f"{row['threads']} thr", 
                               (row['tps'], row['p99']),
                               textcoords="offset points",
                               xytext=(0,10),
                               ha='center')
        
        ax.set_xlabel('Transactions Per Second (TPS)')
        ax.set_ylabel('p99 Latency (μs)')
        ax.set_title(f'TPS vs p99 Latency\nRecord Size: {record_size}B')
        ax.legend()
        ax.grid(True)
        ax.yaxis.set_major_formatter(FuncFormatter(format_latency))
        
        # Save the figure
        filename = f'tps_vs_p99_{record_size}B.png'
        plt.savefig(os.path.join(viz_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()


def visualize_benchmark_data(benchmark_data, output_dir, viz_dir):
    """
    Generate visualizations from benchmark data.
    
    Args:
        benchmark_data: Dictionary containing benchmark data
        output_dir: Directory for output files
        viz_dir: Directory for visualizations
    """
    # Create DataFrames
    hdr_df, log_df = create_dataframes(benchmark_data)
    
    # Set plot style
    set_plot_style()
    
    # Generate visualizations
    print("Generating latency percentiles by thread count charts...")
    plot_latency_percentiles_by_thread_count(hdr_df, viz_dir)
    
    print("Generating TPS by thread count charts...")
    plot_tps_by_thread_count(log_df, viz_dir)
    
    print("Generating latency by record size charts...")
    plot_latency_by_record_size(hdr_df, viz_dir)
    
    print("Generating latency heatmaps...")
    plot_latency_heatmap(hdr_df, viz_dir)
    
    print("Generating TPS heatmaps...")
    plot_tps_heatmap(log_df, viz_dir)
    
    print("Generating latency distribution curves...")
    plot_latency_distribution(hdr_df, benchmark_data, viz_dir)
    
    print("Generating TPS over time charts...")
    plot_tps_over_time(log_df, viz_dir)
    
    print("Generating latency over time charts...")
    plot_latency_over_time(log_df, viz_dir)
    
    print("Generating fill level impact charts...")
    plot_fill_level_impact(hdr_df, viz_dir)
    
    print("Generating comparative analysis charts...")
    plot_comparative_analysis(hdr_df, log_df, viz_dir)
    
    print(f"All visualizations saved to {viz_dir}")


def main():
    """Main function to visualize benchmark data."""
    parser = argparse.ArgumentParser(description='Visualize Aerospike write benchmark data')
    parser.add_argument('--data-dir', default='benchmark_analysis', help='Directory containing benchmark data')
    parser.add_argument('--output-dir', default='benchmark_analysis', help='Directory for output files')
    parser.add_argument('--json-file', default='benchmark_data.json', help='Input JSON file name')
    parser.add_argument('--viz-dir', default='visualizations', help='Directory for visualizations')
    args = parser.parse_args()
    
    # Load benchmark data
    json_path = os.path.join(args.data_dir, args.json_file)
    benchmark_data = load_benchmark_data(json_path)
    
    # Set up visualization directory
    viz_dir = os.path.join(args.output_dir, args.viz_dir)
    os.makedirs(viz_dir, exist_ok=True)
    
    # Generate visualizations
    visualize_benchmark_data(benchmark_data, args.output_dir, viz_dir)


if __name__ == '__main__':
    main()
