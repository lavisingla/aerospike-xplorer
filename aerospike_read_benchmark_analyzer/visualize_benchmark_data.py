#!/usr/bin/env python3
"""
Aerospike Read Benchmark Visualization Script

This script generates visualizations from the extracted benchmark data:
- Latency distribution graphs
- Performance comparison charts
- Heatmaps showing the impact of different parameters

The visualizations are saved as image files for inclusion in reports.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter, ScalarFormatter

class BenchmarkVisualizer:
    def __init__(self, data_file='benchmark_data.json', summary_file='benchmark_summary.csv', output_dir='visualizations'):
        """Initialize the visualizer with the benchmark data files."""
        self.data_file = data_file
        self.summary_file = summary_file
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load data
        self.load_data()
    
    def load_data(self):
        """Load benchmark data from files."""
        # Load JSON data if available
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = None
        
        # Load summary CSV if available
        if os.path.exists(self.summary_file):
            self.summary_df = pd.read_csv(self.summary_file)
        else:
            self.summary_df = None
            
        # Create per-second DataFrame if JSON data is available
        if self.data:
            per_second_rows = []
            
            for key, log_entry in self.data['log_data'].items():
                parts = key.split('_')
                pct = int(parts[0].replace('pct', ''))
                size_bytes = int(parts[1].replace('B', ''))
                threads = int(parts[2].replace('thr', ''))
                
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
            
            self.per_second_df = pd.DataFrame(per_second_rows)
        else:
            self.per_second_df = None
    
    def plot_latency_percentiles_by_threads(self):
        """Plot latency percentiles by thread count for each record size and percentage."""
        if self.summary_df is None:
            print("Summary data not available. Cannot generate latency percentile plots.")
            return
        
        # Get unique combinations of percentage and size
        percentages = sorted(self.summary_df['percentage'].unique())
        sizes = sorted(self.summary_df['size_kb'].unique())
        
        for pct in percentages:
            for size in sizes:
                # Filter data for this percentage and size
                df_filtered = self.summary_df[(self.summary_df['percentage'] == pct) & 
                                             (self.summary_df['size_kb'] == size)]
                
                if len(df_filtered) == 0:
                    continue
                
                # Sort by thread count
                df_filtered = df_filtered.sort_values('threads')
                
                # Create figure
                plt.figure(figsize=(12, 8))
                
                # Plot p50, p90, p99 latencies - convert to ms and apply scaling factor
                plt.plot(df_filtered['threads'], df_filtered['avg_p50_us'] * 0.00125, 'o-', label='p50 Latency')
                plt.plot(df_filtered['threads'], df_filtered['avg_p90_us'] * 0.00125, 's-', label='p90 Latency')
                plt.plot(df_filtered['threads'], df_filtered['avg_p99_us'] * 0.00125, '^-', label='p99 Latency')
                
                # Set labels and title
                plt.xlabel('Thread Count')
                plt.ylabel('Latency (ms)')
                plt.title(f'Latency Percentiles by Thread Count ({pct}% Utilization, {size:.1f} KB Records)')
                
                # Add grid and legend
                plt.grid(True, alpha=0.3)
                plt.legend()
                
                # Use log scale for y-axis if the range is large
                if df_filtered['avg_p99_us'].max() / df_filtered['avg_p50_us'].min() > 10:
                    plt.yscale('log')
                    # Use regular numbers instead of scientific notation
                    ax = plt.gca()
                    ax.yaxis.set_major_formatter(ScalarFormatter())
                    ax.yaxis.get_major_formatter().set_scientific(False)
                    ax.yaxis.get_major_formatter().set_useOffset(False)
                
                # Save figure
                filename = f'latency_percentiles_{pct}pct_{int(size)}kb.png'
                plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
                plt.close()
                
                print(f"Generated {filename}")
    
    def plot_tps_by_threads(self):
        """Plot TPS by thread count for each record size and percentage."""
        if self.summary_df is None:
            print("Summary data not available. Cannot generate TPS plots.")
            return
        
        # Get unique combinations of percentage and size
        percentages = sorted(self.summary_df['percentage'].unique())
        sizes = sorted(self.summary_df['size_kb'].unique())
        
        for pct in percentages:
            # Create figure for this percentage across all sizes
            plt.figure(figsize=(12, 8))
            
            for size in sizes:
                # Filter data for this percentage and size
                df_filtered = self.summary_df[(self.summary_df['percentage'] == pct) & 
                                             (self.summary_df['size_kb'] == size)]
                
                if len(df_filtered) == 0:
                    continue
                
                # Sort by thread count
                df_filtered = df_filtered.sort_values('threads')
                
                # Plot TPS
                plt.plot(df_filtered['threads'], df_filtered['avg_tps'], 'o-', 
                         label=f'{size:.1f} KB Records')
            
            # Set labels and title
            plt.xlabel('Thread Count')
            plt.ylabel('Transactions Per Second (TPS)')
            plt.title(f'Average TPS by Thread Count ({pct}% Utilization)')
            
            # Add grid and legend
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save figure
            filename = f'tps_by_threads_{pct}pct.png'
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
    
    def plot_latency_by_record_size(self):
        """Plot latency by record size for each thread count and percentage."""
        if self.summary_df is None:
            print("Summary data not available. Cannot generate latency by record size plots.")
            return
        
        # Get unique combinations of percentage and threads
        percentages = sorted(self.summary_df['percentage'].unique())
        thread_counts = sorted(self.summary_df['threads'].unique())
        
        for pct in percentages:
            # Create figure for this percentage across all thread counts
            plt.figure(figsize=(12, 8))
            
            for threads in thread_counts:
                # Filter data for this percentage and thread count
                df_filtered = self.summary_df[(self.summary_df['percentage'] == pct) & 
                                             (self.summary_df['threads'] == threads)]
                
                if len(df_filtered) == 0:
                    continue
                
                # Sort by record size
                df_filtered = df_filtered.sort_values('size_kb')
                
                # Plot p99 latency - convert to ms and apply scaling factor
                plt.plot(df_filtered['size_kb'], df_filtered['avg_p99_us'] * 0.00125, 'o-', 
                         label=f'{threads} Threads')
            
            # Set labels and title
            plt.xlabel('Record Size (KB)')
            plt.ylabel('p99 Latency (ms)')
            plt.title(f'p99 Latency by Record Size ({pct}% Utilization)')
            
            # Add grid and legend
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Use log scale for y-axis if the range is large
            if self.summary_df['avg_p99_us'].max() / self.summary_df['avg_p99_us'].min() > 10:
                plt.yscale('log')
                # Use regular numbers instead of scientific notation
                ax = plt.gca()
                ax.yaxis.set_major_formatter(ScalarFormatter())
                ax.yaxis.get_major_formatter().set_scientific(False)
                ax.yaxis.get_major_formatter().set_useOffset(False)
            
            # Save figure
            filename = f'latency_by_size_{pct}pct.png'
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
    
    def plot_latency_heatmap(self):
        """Plot heatmap of latency by thread count and record size for each percentage."""
        if self.summary_df is None:
            print("Summary data not available. Cannot generate latency heatmap.")
            return
        
        # Get unique percentages
        percentages = sorted(self.summary_df['percentage'].unique())
        
        for pct in percentages:
            # Filter data for this percentage
            df_filtered = self.summary_df[self.summary_df['percentage'] == pct]
            
            if len(df_filtered) == 0:
                continue
            
            # Create pivot table for heatmap
            pivot_table = df_filtered.pivot_table(
                values='avg_p99_us', 
                index='threads',
                columns='size_kb',
                aggfunc='mean'
            )
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Create heatmap - convert to ms and apply scaling factor
            sns.heatmap(pivot_table * 0.00125, annot=True, fmt='.2f', cmap='viridis', 
                        cbar_kws={'label': 'p99 Latency (ms)'})
            
            # Set labels and title
            plt.xlabel('Record Size (KB)')
            plt.ylabel('Thread Count')
            plt.title(f'p99 Latency Heatmap ({pct}% Utilization)')
            
            # Save figure
            filename = f'latency_heatmap_{pct}pct.png'
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
    
    def plot_tps_heatmap(self):
        """Plot heatmap of TPS by thread count and record size for each percentage."""
        if self.summary_df is None:
            print("Summary data not available. Cannot generate TPS heatmap.")
            return
        
        # Get unique percentages
        percentages = sorted(self.summary_df['percentage'].unique())
        
        for pct in percentages:
            # Filter data for this percentage
            df_filtered = self.summary_df[self.summary_df['percentage'] == pct]
            
            if len(df_filtered) == 0:
                continue
            
            # Create pivot table for heatmap
            pivot_table = df_filtered.pivot_table(
                values='avg_tps', 
                index='threads',
                columns='size_kb',
                aggfunc='mean'
            )
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Create heatmap
            sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='viridis', 
                        cbar_kws={'label': 'Average TPS'})
            
            # Set labels and title
            plt.xlabel('Record Size (KB)')
            plt.ylabel('Thread Count')
            plt.title(f'Average TPS Heatmap ({pct}% Utilization)')
            
            # Save figure
            filename = f'tps_heatmap_{pct}pct.png'
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
    
    def plot_latency_distribution(self):
        """Plot latency distribution from HDR histogram data for selected configurations."""
        if self.data is None:
            print("HDR data not available. Cannot generate latency distribution plots.")
            return
        
        # Get unique combinations of percentage, size, and threads
        combinations = []
        for key in self.data['hdr_data'].keys():
            parts = key.split('_')
            pct = int(parts[0].replace('pct', ''))
            size_bytes = int(parts[1].replace('B', ''))
            threads = int(parts[2].replace('thr', ''))
            combinations.append((pct, size_bytes, threads))
        
        # Sort combinations
        combinations.sort()
        
        # Select a subset of interesting combinations to plot
        # For each percentage, plot the smallest and largest record size with lowest and highest thread count
        selected_combinations = []
        percentages = sorted(set([c[0] for c in combinations]))
        sizes = sorted(set([c[1] for c in combinations]))
        threads = sorted(set([c[2] for c in combinations]))
        
        for pct in percentages:
            for size in [min(sizes), max(sizes)]:
                for thread in [min(threads), max(threads)]:
                    key = f"{pct}pct_{size}B_thr{thread}"
                    if key in self.data['hdr_data']:
                        selected_combinations.append(key)
        
        # Plot latency distribution for selected combinations
        for key in selected_combinations:
            hdr_entry = self.data['hdr_data'][key]
            percentile_data = hdr_entry['percentile_data']
            
            # Extract percentiles and values - convert to ms and apply scaling factor
            percentiles = [p['percentile'] for p in percentile_data]
            values = [p['value_us'] * 0.00125 for p in percentile_data]  # Convert to ms and apply scaling factor
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Plot latency distribution
            plt.semilogx(values, percentiles, 'o-')
            
            # Use regular numbers instead of scientific notation for x-axis
            ax = plt.gca()
            ax.xaxis.set_major_formatter(ScalarFormatter())
            ax.xaxis.get_major_formatter().set_scientific(False)
            ax.xaxis.get_major_formatter().set_useOffset(False)
            
            # Set labels and title
            parts = key.split('_')
            pct = parts[0]
            size = int(parts[1].replace('B', '')) / 1024
            threads = parts[2].replace('thr', '')
            
            plt.xlabel('Latency (ms)')
            plt.ylabel('Percentile')
            plt.title(f'Latency Distribution ({pct} Utilization, {size:.1f} KB Records, {threads} Threads)')
            
            # Add grid
            plt.grid(True, alpha=0.3)
            
            # Add vertical lines for key percentiles
            p50_value = None
            p90_value = None
            p99_value = None
            
            for p in percentile_data:
                if p['percentile'] == 0.5:
                    p50_value = p['value_us']
                elif p['percentile'] == 0.9:
                    p90_value = p['value_us']
                elif p['percentile'] == 0.99:
                    p99_value = p['value_us']
            
            if p50_value:
                p50_ms = p50_value * 0.00125  # Convert to ms and apply scaling factor
                plt.axvline(p50_ms, color='r', linestyle='--', alpha=0.5, label=f'p50: {p50_ms:.2f} ms')
            if p90_value:
                p90_ms = p90_value * 0.00125  # Convert to ms and apply scaling factor
                plt.axvline(p90_ms, color='g', linestyle='--', alpha=0.5, label=f'p90: {p90_ms:.2f} ms')
            if p99_value:
                p99_ms = p99_value * 0.00125  # Convert to ms and apply scaling factor
                plt.axvline(p99_ms, color='b', linestyle='--', alpha=0.5, label=f'p99: {p99_ms:.2f} ms')
            
            plt.legend()
            
            # Save figure
            filename = f'latency_distribution_{key}.png'
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
    
    def plot_tps_over_time(self):
        """Plot TPS over time for selected configurations."""
        if self.per_second_df is None:
            print("Per-second data not available. Cannot generate TPS over time plots.")
            return
        
        # Get unique combinations of percentage, size, and threads
        combinations = self.per_second_df.groupby(['percentage', 'size_kb', 'threads']).size().reset_index().rename(columns={0: 'count'})
        
        # Select a subset of interesting combinations to plot
        # For each percentage, plot the smallest and largest record size with lowest and highest thread count
        percentages = sorted(combinations['percentage'].unique())
        sizes = sorted(combinations['size_kb'].unique())
        threads = sorted(combinations['threads'].unique())
        
        selected_combinations = []
        for pct in percentages:
            for size in [min(sizes), max(sizes)]:
                for thread in [min(threads), max(threads)]:
                    selected_combinations.append((pct, size, thread))
        
        # Plot TPS over time for selected combinations
        for pct, size, thread in selected_combinations:
            # Filter data for this combination
            df_filtered = self.per_second_df[
                (self.per_second_df['percentage'] == pct) & 
                (self.per_second_df['size_kb'] == size) & 
                (self.per_second_df['threads'] == thread)
            ]
            
            if len(df_filtered) == 0:
                continue
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Plot TPS over time
            plt.plot(df_filtered['seconds'], df_filtered['tps'], 'o-')
            
            # Set labels and title
            plt.xlabel('Time (seconds)')
            plt.ylabel('Transactions Per Second (TPS)')
            plt.title(f'TPS Over Time ({pct}% Utilization, {size:.1f} KB Records, {thread} Threads)')
            
            # Add grid
            plt.grid(True, alpha=0.3)
            
            # Add horizontal line for average TPS
            avg_tps = df_filtered['tps'].mean()
            plt.axhline(avg_tps, color='r', linestyle='--', alpha=0.5, label=f'Avg TPS: {avg_tps:.0f}')
            
            plt.legend()
            
            # Save figure
            filename = f'tps_over_time_{pct}pct_{int(size)}kb_thr{thread}.png'
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
    
    def plot_latency_over_time(self):
        """Plot latency percentiles over time for selected configurations."""
        if self.per_second_df is None:
            print("Per-second data not available. Cannot generate latency over time plots.")
            return
        
        # Get unique combinations of percentage, size, and threads
        combinations = self.per_second_df.groupby(['percentage', 'size_kb', 'threads']).size().reset_index().rename(columns={0: 'count'})
        
        # Select a subset of interesting combinations to plot
        # For each percentage, plot the smallest and largest record size with lowest and highest thread count
        percentages = sorted(combinations['percentage'].unique())
        sizes = sorted(combinations['size_kb'].unique())
        threads = sorted(combinations['threads'].unique())
        
        selected_combinations = []
        for pct in percentages:
            for size in [min(sizes), max(sizes)]:
                for thread in [min(threads), max(threads)]:
                    selected_combinations.append((pct, size, thread))
        
        # Plot latency over time for selected combinations
        for pct, size, thread in selected_combinations:
            # Filter data for this combination
            df_filtered = self.per_second_df[
                (self.per_second_df['percentage'] == pct) & 
                (self.per_second_df['size_kb'] == size) & 
                (self.per_second_df['threads'] == thread)
            ]
            
            if len(df_filtered) == 0:
                continue
            
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Plot p50, p90, p99 latencies over time - convert to ms and apply scaling factor
            plt.plot(df_filtered['seconds'], df_filtered['p50'] * 0.00125, 'o-', label='p50 Latency')
            plt.plot(df_filtered['seconds'], df_filtered['p90'] * 0.00125, 's-', label='p90 Latency')
            plt.plot(df_filtered['seconds'], df_filtered['p99'] * 0.00125, '^-', label='p99 Latency')
            
            # Set labels and title
            plt.xlabel('Time (seconds)')
            plt.ylabel('Latency (ms)')
            plt.title(f'Latency Percentiles Over Time ({pct}% Utilization, {size:.1f} KB Records, {thread} Threads)')
            
            # Add grid and legend
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Use log scale for y-axis if the range is large
            if df_filtered['p99'].max() / df_filtered['p50'].min() > 10:
                plt.yscale('log')
                # Use regular numbers instead of scientific notation
                ax = plt.gca()
                ax.yaxis.set_major_formatter(ScalarFormatter())
                ax.yaxis.get_major_formatter().set_scientific(False)
                ax.yaxis.get_major_formatter().set_useOffset(False)
            
            # Save figure
            filename = f'latency_over_time_{pct}pct_{int(size)}kb_thr{thread}.png'
            plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Generated {filename}")
    
    def plot_comparative_bar_charts(self):
        """Plot comparative bar charts for different configurations."""
        if self.summary_df is None:
            print("Summary data not available. Cannot generate comparative bar charts.")
            return
        
        # Plot p99 latency comparison by record size for each percentage (with thread count = 50)
        thread_count = 50  # Choose a representative thread count
        
        # Get unique percentages
        percentages = sorted(self.summary_df['percentage'].unique())
        
        # Create figure
        plt.figure(figsize=(14, 10))
        
        # Set up bar positions
        bar_width = 0.25
        sizes = sorted(self.summary_df['size_kb'].unique())
        x = np.arange(len(sizes))
        
        # Plot bars for each percentage
        for i, pct in enumerate(percentages):
            # Filter data for this percentage and thread count
            df_filtered = self.summary_df[
                (self.summary_df['percentage'] == pct) & 
                (self.summary_df['threads'] == thread_count)
            ]
            
            if len(df_filtered) == 0:
                continue
            
            # Sort by record size
            df_filtered = df_filtered.sort_values('size_kb')
            
            # Get p99 latencies
            latencies = []
            for size in sizes:
                row = df_filtered[df_filtered['size_kb'] == size]
                if len(row) > 0:
                    latencies.append(row['avg_p99_us'].values[0])
                else:
                    latencies.append(0)
            
            # Plot bars - convert to ms and apply scaling factor
            plt.bar(x + (i - 1) * bar_width, [lat * 0.00125 for lat in latencies], bar_width, label=f'{pct}% Utilization')
        
        # Set labels and title
        plt.xlabel('Record Size (KB)')
        plt.ylabel('p99 Latency (ms)')
        plt.title(f'p99 Latency Comparison by Record Size (Thread Count: {thread_count})')
        
        # Set x-tick labels
        plt.xticks(x, [f'{size:.1f}' for size in sizes])
        
        # Add grid and legend
        plt.grid(True, alpha=0.3, axis='y')
        plt.legend()
        
        # Save figure
        filename = f'p99_latency_comparison_thr{thread_count}.png'
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Generated {filename}")
        
        # Plot TPS comparison by thread count for each percentage (with record size = 8KB)
        record_size = 8.0  # Choose a representative record size
        
        # Create figure
        plt.figure(figsize=(14, 10))
        
        # Set up bar positions
        thread_counts = sorted(self.summary_df['threads'].unique())
        x = np.arange(len(thread_counts))
        
        # Plot bars for each percentage
        for i, pct in enumerate(percentages):
            # Filter data for this percentage and record size
            df_filtered = self.summary_df[
                (self.summary_df['percentage'] == pct) & 
                (self.summary_df['size_kb'] == record_size)
            ]
            
            if len(df_filtered) == 0:
                continue
            
            # Sort by thread count
            df_filtered = df_filtered.sort_values('threads')
            
            # Get TPS values
            tps_values = []
            for threads in thread_counts:
                row = df_filtered[df_filtered['threads'] == threads]
                if len(row) > 0:
                    tps_values.append(row['avg_tps'].values[0])
                else:
                    tps_values.append(0)
            
            # Plot bars
            plt.bar(x + (i - 1) * bar_width, tps_values, bar_width, label=f'{pct}% Utilization')
        
        # Set labels and title
        plt.xlabel('Thread Count')
        plt.ylabel('Average TPS')
        plt.title(f'TPS Comparison by Thread Count (Record Size: {record_size:.1f} KB)')
        
        # Set x-tick labels
        plt.xticks(x, [str(tc) for tc in thread_counts])
        
        # Add grid and legend
        plt.grid(True, alpha=0.3, axis='y')
        plt.legend()
        
        # Save figure
        filename = f'tps_comparison_{int(record_size)}kb.png'
        plt.savefig(os.path.join(self.output_dir, filename), dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Generated {filename}")
    
    def generate_all_visualizations(self):
        """Generate all visualizations."""
        print("Generating latency percentiles by threads plots...")
        self.plot_latency_percentiles_by_threads()
        
        print("\nGenerating TPS by threads plots...")
        self.plot_tps_by_threads()
        
        print("\nGenerating latency by record size plots...")
        self.plot_latency_by_record_size()
        
        print("\nGenerating latency heatmaps...")
        self.plot_latency_heatmap()
        
        print("\nGenerating TPS heatmaps...")
        self.plot_tps_heatmap()
        
        print("\nGenerating latency distribution plots...")
        self.plot_latency_distribution()
        
        print("\nGenerating TPS over time plots...")
        self.plot_tps_over_time()
        
        print("\nGenerating latency over time plots...")
        self.plot_latency_over_time()
        
        print("\nGenerating comparative bar charts...")
        self.plot_comparative_bar_charts()
        
        print("\nAll visualizations generated successfully!")

def main():
    """Main function to generate visualizations from benchmark data."""
    visualizer = BenchmarkVisualizer()
    visualizer.generate_all_visualizations()

if __name__ == "__main__":
    main()
