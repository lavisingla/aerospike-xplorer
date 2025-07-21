#!/usr/bin/env python3
"""
Aerospike Read Benchmark Report Generator

This script generates a comprehensive HTML report from the benchmark data and visualizations:
- Summary statistics and key findings
- Comparative analysis across different configurations
- Embedded visualizations
- Recommendations based on the benchmark results
"""

import os
import json
import pandas as pd
import numpy as np
import glob
from datetime import datetime
from jinja2 import Template

class BenchmarkReportGenerator:
    def __init__(self, data_file='benchmark_data.json', summary_file='benchmark_summary.csv', 
                 visualizations_dir='visualizations', output_file='benchmark_report.html'):
        """Initialize the report generator with the benchmark data files."""
        self.data_file = data_file
        self.summary_file = summary_file
        self.visualizations_dir = visualizations_dir
        self.output_file = output_file
        
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
    
    def get_visualization_paths(self):
        """Get paths to all visualization images."""
        if not os.path.exists(self.visualizations_dir):
            return []
        
        return sorted(glob.glob(os.path.join(self.visualizations_dir, '*.png')))
    
    def calculate_key_statistics(self):
        """Calculate key statistics from the benchmark data."""
        if self.summary_df is None:
            return {}
        
        stats = {}
        
        # Overall statistics
        stats['total_configs'] = len(self.summary_df)
        stats['avg_tps_overall'] = self.summary_df['avg_tps'].mean()
        stats['max_tps'] = self.summary_df['max_tps'].max()
        stats['min_p99_latency'] = self.summary_df['avg_p99_us'].min() * 0.00125  # Convert to ms and apply scaling factor
        
        # Configuration with max TPS
        max_tps_row = self.summary_df.loc[self.summary_df['max_tps'].idxmax()]
        stats['max_tps_config'] = {
            'percentage': max_tps_row['percentage'],
            'size_kb': max_tps_row['size_kb'],
            'threads': max_tps_row['threads'],
            'tps': max_tps_row['max_tps']
        }
        
        # Configuration with min p99 latency
        min_p99_row = self.summary_df.loc[self.summary_df['avg_p99_us'].idxmin()]
        stats['min_p99_config'] = {
            'percentage': min_p99_row['percentage'],
            'size_kb': min_p99_row['size_kb'],
            'threads': min_p99_row['threads'],
            'latency': min_p99_row['avg_p99_us'] * 0.00125  # Convert to ms and apply scaling factor
        }
        
        # Statistics by percentage
        stats['by_percentage'] = {}
        for pct in sorted(self.summary_df['percentage'].unique()):
            df_pct = self.summary_df[self.summary_df['percentage'] == pct]
            stats['by_percentage'][pct] = {
                'avg_tps': df_pct['avg_tps'].mean(),
                'max_tps': df_pct['max_tps'].max(),
                'avg_p99_latency': df_pct['avg_p99_us'].mean() * 0.00125,  # Convert to ms and apply scaling factor
                'min_p99_latency': df_pct['avg_p99_us'].min() * 0.00125    # Convert to ms and apply scaling factor
            }
        
        # Statistics by record size
        stats['by_size'] = {}
        for size in sorted(self.summary_df['size_kb'].unique()):
            df_size = self.summary_df[self.summary_df['size_kb'] == size]
            stats['by_size'][size] = {
                'avg_tps': df_size['avg_tps'].mean(),
                'max_tps': df_size['max_tps'].max(),
                'avg_p99_latency': df_size['avg_p99_us'].mean() * 0.00125,  # Convert to ms and apply scaling factor
                'min_p99_latency': df_size['avg_p99_us'].min() * 0.00125    # Convert to ms and apply scaling factor
            }
        
        # Statistics by thread count
        stats['by_threads'] = {}
        for threads in sorted(self.summary_df['threads'].unique()):
            df_threads = self.summary_df[self.summary_df['threads'] == threads]
            stats['by_threads'][threads] = {
                'avg_tps': df_threads['avg_tps'].mean(),
                'max_tps': df_threads['max_tps'].max(),
                'avg_p99_latency': df_threads['avg_p99_us'].mean() * 0.00125,  # Convert to ms and apply scaling factor
                'min_p99_latency': df_threads['avg_p99_us'].min() * 0.00125    # Convert to ms and apply scaling factor
            }
        
        # Find optimal configurations
        # For each record size, find the thread count that gives the best performance
        stats['optimal_configs'] = {}
        for size in sorted(self.summary_df['size_kb'].unique()):
            stats['optimal_configs'][size] = {}
            for pct in sorted(self.summary_df['percentage'].unique()):
                df_filtered = self.summary_df[(self.summary_df['size_kb'] == size) & 
                                             (self.summary_df['percentage'] == pct)]
                if len(df_filtered) == 0:
                    continue
                
                # Find thread count with max TPS
                max_tps_row = df_filtered.loc[df_filtered['avg_tps'].idxmax()]
                
                # Find thread count with min p99 latency
                min_p99_row = df_filtered.loc[df_filtered['avg_p99_us'].idxmin()]
                
                stats['optimal_configs'][size][pct] = {
                    'max_tps_threads': max_tps_row['threads'],
                    'max_tps': max_tps_row['avg_tps'],
                    'min_p99_threads': min_p99_row['threads'],
                    'min_p99_latency': min_p99_row['avg_p99_us'] * 0.00125  # Convert to ms and apply scaling factor
                }
        
        return stats
    
    def generate_insights(self, stats):
        """Generate insights based on the statistics."""
        if not stats:
            return []
        
        insights = []
        
        # Impact of thread count on performance
        thread_counts = sorted(stats['by_threads'].keys())
        if len(thread_counts) > 1:
            tps_values = [stats['by_threads'][t]['avg_tps'] for t in thread_counts]
            latency_values = [stats['by_threads'][t]['avg_p99_latency'] for t in thread_counts]
            
            # Check if TPS increases with thread count
            if tps_values[-1] > tps_values[0]:
                insights.append("Increasing thread count generally improves throughput (TPS).")
            else:
                insights.append("Increasing thread count beyond a certain point does not improve throughput.")
            
            # Check if latency increases with thread count
            if latency_values[-1] > latency_values[0]:
                insights.append("Higher thread counts result in increased latency.")
            
            # Find optimal thread count for throughput
            max_tps_thread = thread_counts[tps_values.index(max(tps_values))]
            insights.append(f"The optimal thread count for maximum throughput is {max_tps_thread}.")
            
            # Find optimal thread count for latency
            min_latency_thread = thread_counts[latency_values.index(min(latency_values))]
            insights.append(f"The optimal thread count for minimum latency is {min_latency_thread}.")
        
        # Impact of record size on performance
        sizes = sorted(stats['by_size'].keys())
        if len(sizes) > 1:
            tps_values = [stats['by_size'][s]['avg_tps'] for s in sizes]
            latency_values = [stats['by_size'][s]['avg_p99_latency'] for s in sizes]
            
            # Check if TPS decreases with record size
            if tps_values[-1] < tps_values[0]:
                insights.append("Larger record sizes result in lower throughput (TPS).")
            
            # Check if latency increases with record size
            if latency_values[-1] > latency_values[0]:
                insights.append("Larger record sizes result in higher latency.")
            
            # Calculate percentage decrease in TPS from smallest to largest record size
            tps_decrease_pct = (tps_values[0] - tps_values[-1]) / tps_values[0] * 100
            insights.append(f"Increasing record size from {sizes[0]:.1f} KB to {sizes[-1]:.1f} KB results in a {tps_decrease_pct:.1f}% decrease in throughput.")
            
            # Calculate percentage increase in latency from smallest to largest record size
            latency_increase_pct = (latency_values[-1] - latency_values[0]) / latency_values[0] * 100
            insights.append(f"Increasing record size from {sizes[0]:.1f} KB to {sizes[-1]:.1f} KB results in a {latency_increase_pct:.1f}% increase in p99 latency.")
        
        # Impact of storage utilization on performance
        percentages = sorted(stats['by_percentage'].keys())
        if len(percentages) > 1:
            tps_values = [stats['by_percentage'][p]['avg_tps'] for p in percentages]
            latency_values = [stats['by_percentage'][p]['avg_p99_latency'] for p in percentages]
            
            # Check if TPS decreases with storage utilization
            if tps_values[-1] < tps_values[0]:
                insights.append("Higher storage utilization results in lower throughput (TPS).")
            
            # Check if latency increases with storage utilization
            if latency_values[-1] > latency_values[0]:
                insights.append("Higher storage utilization results in higher latency.")
            
            # Calculate percentage decrease in TPS from lowest to highest utilization
            tps_decrease_pct = (tps_values[0] - tps_values[-1]) / tps_values[0] * 100
            insights.append(f"Increasing storage utilization from {percentages[0]}% to {percentages[-1]}% results in a {tps_decrease_pct:.1f}% decrease in throughput.")
            
            # Calculate percentage increase in latency from lowest to highest utilization
            latency_increase_pct = (latency_values[-1] - latency_values[0]) / latency_values[0] * 100
            insights.append(f"Increasing storage utilization from {percentages[0]}% to {percentages[-1]}% results in a {latency_increase_pct:.1f}% increase in p99 latency.")
        
        return insights
    
    def generate_recommendations(self, stats):
        """Generate recommendations based on the statistics."""
        if not stats:
            return []
        
        recommendations = []
        
        # Recommend optimal thread count based on record size
        recommendations.append("Optimal Thread Count Recommendations:")
        for size in sorted(stats['optimal_configs'].keys()):
            size_recommendations = []
            for pct in sorted(stats['optimal_configs'][size].keys()):
                config = stats['optimal_configs'][size][pct]
                
                # If the same thread count is optimal for both TPS and latency
                if config['max_tps_threads'] == config['min_p99_threads']:
                    size_recommendations.append(f"For {pct}% utilization, use {config['max_tps_threads']} threads for optimal performance.")
                else:
                    # If different thread counts are optimal for TPS and latency
                    size_recommendations.append(f"For {pct}% utilization, use {config['max_tps_threads']} threads for maximum throughput or {config['min_p99_threads']} threads for minimum latency.")
            
            if size_recommendations:
                recommendations.append(f"For {size:.1f} KB records:")
                recommendations.extend([f"  - {rec}" for rec in size_recommendations])
        
        # General recommendations
        recommendations.append("\nGeneral Recommendations:")
        
        # Recommend based on storage utilization
        percentages = sorted(stats['by_percentage'].keys())
        if len(percentages) > 1:
            best_pct = min(percentages, key=lambda p: stats['by_percentage'][p]['avg_p99_latency'])
            recommendations.append(f"  - For best performance, maintain storage utilization at or below {best_pct}%.")
        
        # Recommend based on thread count
        thread_counts = sorted(stats['by_threads'].keys())
        if len(thread_counts) > 1:
            # Find thread count with best throughput/latency balance
            thread_scores = {}
            for t in thread_counts:
                # Normalize TPS and latency (higher is better for both)
                norm_tps = stats['by_threads'][t]['avg_tps'] / stats['max_tps']
                norm_latency = min([stats['by_threads'][tc]['avg_p99_latency'] for tc in thread_counts]) / stats['by_threads'][t]['avg_p99_latency']
                # Calculate score (weighted average)
                thread_scores[t] = 0.6 * norm_tps + 0.4 * norm_latency
            
            best_thread = max(thread_scores, key=thread_scores.get)
            recommendations.append(f"  - For a good balance of throughput and latency, use approximately {best_thread} threads.")
        
        # Recommend based on record size
        sizes = sorted(stats['by_size'].keys())
        if len(sizes) > 1:
            recommendations.append(f"  - Smaller record sizes ({sizes[0]:.1f} KB) provide significantly better performance than larger ones ({sizes[-1]:.1f} KB).")
            recommendations.append(f"  - If possible, consider splitting large records into smaller ones to improve performance.")
        
        return recommendations
    
    def generate_html_report(self):
        """Generate HTML report from the benchmark data and visualizations."""
        # Calculate statistics
        stats = self.calculate_key_statistics()
        
        # Generate insights and recommendations
        insights = self.generate_insights(stats)
        recommendations = self.generate_recommendations(stats)
        
        # Get visualization paths
        visualization_paths = self.get_visualization_paths()
        
        # Group visualizations by type
        visualization_groups = {
            'latency_percentiles': [],
            'tps_by_threads': [],
            'latency_by_size': [],
            'latency_heatmap': [],
            'tps_heatmap': [],
            'latency_distribution': [],
            'tps_over_time': [],
            'latency_over_time': [],
            'comparative': []
        }
        
        for path in visualization_paths:
            filename = os.path.basename(path)
            if filename.startswith('latency_percentiles_'):
                visualization_groups['latency_percentiles'].append(path)
            elif filename.startswith('tps_by_threads_'):
                visualization_groups['tps_by_threads'].append(path)
            elif filename.startswith('latency_by_size_'):
                visualization_groups['latency_by_size'].append(path)
            elif filename.startswith('latency_heatmap_'):
                visualization_groups['latency_heatmap'].append(path)
            elif filename.startswith('tps_heatmap_'):
                visualization_groups['tps_heatmap'].append(path)
            elif filename.startswith('latency_distribution_'):
                visualization_groups['latency_distribution'].append(path)
            elif filename.startswith('tps_over_time_'):
                visualization_groups['tps_over_time'].append(path)
            elif filename.startswith('latency_over_time_'):
                visualization_groups['latency_over_time'].append(path)
            elif filename.startswith('p99_latency_comparison_') or filename.startswith('tps_comparison_'):
                visualization_groups['comparative'].append(path)
        
        # Create summary tables
        summary_tables = {}
        
        if self.summary_df is not None:
            # Table by percentage and record size (showing thread count with max TPS)
            pivot_max_tps = self.summary_df.pivot_table(
                values='avg_tps',
                index='percentage',
                columns='size_kb',
                aggfunc='max'
            )
            summary_tables['max_tps'] = pivot_max_tps.to_html(classes='table table-striped table-bordered')
            
            # Table by percentage and record size (showing thread count with min p99 latency)
            # Apply conversion factor to convert from μs to ms and scale by 1.25
            min_p99_values = self.summary_df.pivot_table(
                values='avg_p99_us',
                index='percentage',
                columns='size_kb',
                aggfunc='min'
            ) * 0.00125
            pivot_min_p99 = min_p99_values
            summary_tables['min_p99'] = pivot_min_p99.to_html(classes='table table-striped table-bordered')
            
            # Table showing optimal thread count for each percentage and record size
            optimal_threads = pd.DataFrame(index=sorted(self.summary_df['percentage'].unique()),
                                          columns=sorted(self.summary_df['size_kb'].unique()))
            
            for pct in optimal_threads.index:
                for size in optimal_threads.columns:
                    df_filtered = self.summary_df[(self.summary_df['percentage'] == pct) & 
                                                 (self.summary_df['size_kb'] == size)]
                    if len(df_filtered) > 0:
                        max_tps_row = df_filtered.loc[df_filtered['avg_tps'].idxmax()]
                        min_p99_row = df_filtered.loc[df_filtered['avg_p99_us'].idxmin()]
                        
                        if max_tps_row['threads'] == min_p99_row['threads']:
                            optimal_threads.at[pct, size] = f"{int(max_tps_row['threads'])}"
                        else:
                            optimal_threads.at[pct, size] = f"{int(max_tps_row['threads'])} (TPS) / {int(min_p99_row['threads'])} (p99)"
            
            summary_tables['optimal_threads'] = optimal_threads.to_html(classes='table table-striped table-bordered')
        
        # HTML template
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aerospike Read Benchmark Report</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1, h2, h3, h4 {
                    color: #0066cc;
                }
                .section {
                    margin-bottom: 30px;
                }
                .visualization {
                    margin: 20px 0;
                    text-align: center;
                }
                .visualization img {
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }
                .table-container {
                    overflow-x: auto;
                    margin: 20px 0;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ddd;
                }
                th {
                    background-color: #f2f2f2;
                }
                .insight, .recommendation {
                    padding: 10px;
                    margin: 5px 0;
                    border-left: 4px solid #0066cc;
                    background-color: #f8f9fa;
                }
                .key-stat {
                    display: inline-block;
                    margin: 10px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    box-shadow: 0 0 5px rgba(0,0,0,0.1);
                    min-width: 200px;
                }
                .key-stat h4 {
                    margin-top: 0;
                }
                .key-stat p {
                    font-size: 24px;
                    font-weight: bold;
                    margin: 5px 0;
                }
                .key-stat small {
                    font-size: 14px;
                    color: #666;
                }
                .footer {
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="section">
                <h1>Aerospike Read Benchmark Report</h1>
                <p>Generated on {{ date }}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <p>This report presents the results of Aerospike read benchmark tests across various configurations, including different storage utilization levels, record sizes, and thread counts.</p>
                
                <div class="key-stats">
                    <div class="key-stat">
                        <h4>Configurations Tested</h4>
                        <p>{{ stats.total_configs }}</p>
                    </div>
                    <div class="key-stat">
                        <h4>Maximum TPS</h4>
                        <p>{{ stats.max_tps|int }}</p>
                        <small>{{ stats.max_tps_config.percentage }}% utilization, {{ stats.max_tps_config.size_kb }} KB, {{ stats.max_tps_config.threads }} threads</small>
                    </div>
                    <div class="key-stat">
                    <h4>Minimum p99 Latency</h4>
                    <p>{{ stats.min_p99_latency|float|round(2) }} ms</p>
                    <small>{{ stats.min_p99_config.percentage }}% utilization, {{ stats.min_p99_config.size_kb }} KB, {{ stats.min_p99_config.threads }} threads</small>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Key Insights</h2>
                {% for insight in insights %}
                <div class="insight">{{ insight }}</div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                {% for recommendation in recommendations %}
                <div class="recommendation">{{ recommendation }}</div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>Summary Tables</h2>
                
                <h3>Maximum TPS by Storage Utilization and Record Size</h3>
                <div class="table-container">
                    {{ summary_tables.max_tps|safe }}
                </div>
                
                <h3>Minimum p99 Latency (ms) by Storage Utilization and Record Size</h3>
                <div class="table-container">
                    {{ summary_tables.min_p99|safe }}
                </div>
                
                <h3>Optimal Thread Count by Storage Utilization and Record Size</h3>
                <div class="table-container">
                    {{ summary_tables.optimal_threads|safe }}
                </div>
            </div>
            
            <div class="section">
                <h2>Performance Analysis</h2>
                
                <h3>Latency Percentiles by Thread Count</h3>
                <p>These charts show how different latency percentiles (p50, p90, p99) change with increasing thread count for different record sizes and storage utilization levels.</p>
                {% for viz in visualization_groups.latency_percentiles %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="Latency Percentiles Chart">
                </div>
                {% endfor %}
                
                <h3>TPS by Thread Count</h3>
                <p>These charts show how throughput (TPS) changes with increasing thread count for different record sizes and storage utilization levels.</p>
                {% for viz in visualization_groups.tps_by_threads %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="TPS by Thread Count Chart">
                </div>
                {% endfor %}
                
                <h3>Latency by Record Size</h3>
                <p>These charts show how p99 latency changes with increasing record size for different thread counts and storage utilization levels.</p>
                {% for viz in visualization_groups.latency_by_size %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="Latency by Record Size Chart">
                </div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>Heatmaps</h2>
                
                <h3>Latency Heatmaps</h3>
                <p>These heatmaps show p99 latency for different combinations of thread count and record size at various storage utilization levels.</p>
                {% for viz in visualization_groups.latency_heatmap %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="Latency Heatmap">
                </div>
                {% endfor %}
                
                <h3>TPS Heatmaps</h3>
                <p>These heatmaps show average TPS for different combinations of thread count and record size at various storage utilization levels.</p>
                {% for viz in visualization_groups.tps_heatmap %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="TPS Heatmap">
                </div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>Detailed Analysis</h2>
                
                <h3>Latency Distribution</h3>
                <p>These charts show the full latency distribution (percentile curves) for selected configurations.</p>
                {% for viz in visualization_groups.latency_distribution %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="Latency Distribution Chart">
                </div>
                {% endfor %}
                
                <h3>TPS Over Time</h3>
                <p>These charts show how TPS varies over time during the benchmark for selected configurations.</p>
                {% for viz in visualization_groups.tps_over_time %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="TPS Over Time Chart">
                </div>
                {% endfor %}
                
                <h3>Latency Over Time</h3>
                <p>These charts show how latency percentiles vary over time during the benchmark for selected configurations.</p>
                {% for viz in visualization_groups.latency_over_time %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="Latency Over Time Chart">
                </div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>Comparative Analysis</h2>
                <p>These charts provide direct comparisons between different configurations.</p>
                {% for viz in visualization_groups.comparative %}
                <div class="visualization">
                    <img src="{{ viz }}" alt="Comparative Chart">
                </div>
                {% endfor %}
            </div>
            
            <div class="footer">
                <p>Aerospike Read Benchmark Report | Generated on {{ date }}</p>
            </div>
        </body>
        </html>
        """
        
        # Render template
        template = Template(template_str)
        html_content = template.render(
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            stats=stats,
            insights=insights,
            recommendations=recommendations,
            visualization_groups=visualization_groups,
            summary_tables=summary_tables
        )
        
        # Write HTML report to file
        with open(self.output_file, 'w') as f:
            f.write(html_content)
        
        return self.output_file

def main():
    """Main function to generate benchmark report."""
    report_generator = BenchmarkReportGenerator()
    report_file = report_generator.generate_html_report()
    print(f"Benchmark report generated: {report_file}")

if __name__ == "__main__":
    main()
