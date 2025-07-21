#!/usr/bin/env python3
"""
Generate benchmark report from Aerospike write latency data.

This script creates a comprehensive HTML report with summary statistics,
insights, and recommendations based on the benchmark data and visualizations.
"""

import os
import json
import argparse
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader
import webbrowser
from datetime import datetime


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


def format_latency(value):
    """Format latency values for display."""
    if value is None:
        return "N/A"
    
    if value >= 1000000:
        return f'{value/1000000:.2f} s'
    elif value >= 1000:
        return f'{value/1000:.2f} ms'
    else:
        return f'{value:.0f} μs'


def generate_summary_statistics(hdr_df, log_df):
    """
    Generate summary statistics from benchmark data.
    
    Args:
        hdr_df: DataFrame containing HDR data
        log_df: DataFrame containing log data
        
    Returns:
        dict: Dictionary containing summary statistics
    """
    # Calculate average TPS for each configuration
    tps_avg = log_df.groupby(['record_size', 'target_pct', 'threads'])['tps'].mean().reset_index()
    
    # Find best TPS configuration
    if not tps_avg.empty and not tps_avg['tps'].isna().all():
        best_tps_row = tps_avg.loc[tps_avg['tps'].idxmax()]
        best_tps_config = {
            'record_size': best_tps_row['record_size'],
            'target_pct': best_tps_row['target_pct'],
            'threads': best_tps_row['threads'],
            'tps': best_tps_row['tps']
        }
    else:
        best_tps_config = {
            'record_size': None,
            'target_pct': None,
            'threads': None,
            'tps': None
        }
    
    # Find best latency configurations
    percentiles = ['p50', 'p99', 'p99.9']
    best_latency_configs = {}
    
    for percentile in percentiles:
        # Check if we have valid data for this percentile
        if not hdr_df.empty and not hdr_df[percentile].isna().all():
            best_latency_row = hdr_df.loc[hdr_df[percentile].idxmin()]
            best_latency_configs[percentile] = {
                'record_size': best_latency_row['record_size'],
                'target_pct': best_latency_row['target_pct'],
                'threads': best_latency_row['threads'],
                'latency': best_latency_row[percentile]
            }
        else:
            best_latency_configs[percentile] = {
                'record_size': None,
                'target_pct': None,
                'threads': None,
                'latency': None
            }
    
    # Calculate overall statistics
    overall_stats = {
        'total_configs': len(hdr_df),
        'record_sizes': sorted(hdr_df['record_size'].unique()),
        'thread_counts': sorted(hdr_df['threads'].unique()),
        'fill_levels': sorted(hdr_df['target_pct'].unique()),
        'avg_p50': hdr_df['p50'].mean() if not hdr_df.empty and not hdr_df['p50'].isna().all() else None,
        'avg_p99': hdr_df['p99'].mean() if not hdr_df.empty and not hdr_df['p99'].isna().all() else None,
        'avg_p99_9': hdr_df['p99.9'].mean() if not hdr_df.empty and not hdr_df['p99.9'].isna().all() else None,
        'avg_tps': tps_avg['tps'].mean() if not tps_avg.empty and not tps_avg['tps'].isna().all() else None,
        'max_tps': tps_avg['tps'].max() if not tps_avg.empty and not tps_avg['tps'].isna().all() else None,
        'min_p50': hdr_df['p50'].min() if not hdr_df.empty and not hdr_df['p50'].isna().all() else None,
        'min_p99': hdr_df['p99'].min() if not hdr_df.empty and not hdr_df['p99'].isna().all() else None,
        'min_p99_9': hdr_df['p99.9'].min() if not hdr_df.empty and not hdr_df['p99.9'].isna().all() else None
    }
    
    return {
        'best_tps_config': best_tps_config,
        'best_latency_configs': best_latency_configs,
        'overall_stats': overall_stats
    }


def generate_insights(hdr_df, log_df, summary_stats):
    """
    Generate insights from benchmark data.
    
    Args:
        hdr_df: DataFrame containing HDR data
        log_df: DataFrame containing log data
        summary_stats: Dictionary containing summary statistics
        
    Returns:
        list: List of insights
    """
    insights = []
    
    # Calculate average TPS for each configuration
    tps_avg = log_df.groupby(['record_size', 'target_pct', 'threads'])['tps'].mean().reset_index()
    
    # Merge with HDR data
    merged_df = pd.merge(
        hdr_df,
        tps_avg,
        on=['record_size', 'target_pct', 'threads'],
        how='inner'
    )
    
    # Insight 1: Impact of thread count on TPS
    thread_counts = sorted(merged_df['threads'].unique())
    if len(thread_counts) > 1:
        tps_by_thread = merged_df.groupby('threads')['tps'].mean()
        max_thread = tps_by_thread.idxmax()
        max_tps = tps_by_thread.max()
        min_thread = tps_by_thread.idxmin()
        min_tps = tps_by_thread.min()
        
        if max_thread == thread_counts[-1]:
            insight = (f"Increasing thread count generally improves write throughput, with {max_thread} threads "
                      f"achieving the highest average TPS of {max_tps:.0f}. This suggests that the system may "
                      f"benefit from even more threads.")
        elif max_thread == thread_counts[0]:
            insight = (f"Lower thread counts perform better for write operations, with {max_thread} threads "
                      f"achieving the highest average TPS of {max_tps:.0f}. Higher thread counts may lead to "
                      f"contention and reduced performance.")
        else:
            insight = (f"The optimal thread count for write operations is around {max_thread}, "
                      f"achieving an average TPS of {max_tps:.0f}. Both lower and higher thread counts "
                      f"show reduced performance, suggesting a sweet spot for concurrency.")
        
        insights.append(insight)
    
    # Insight 2: Impact of record size on latency
    record_sizes = sorted(merged_df['record_size'].unique())
    if len(record_sizes) > 1:
        p99_by_size = merged_df.groupby('record_size')['p99'].mean()
        
        if not p99_by_size.isna().all():
            min_size = p99_by_size.idxmin()
            min_p99 = p99_by_size.min()
            max_size = p99_by_size.idxmax()
            max_p99 = p99_by_size.max()
            
            insight = (f"Record size significantly impacts write latency. {min_size}B records show the lowest "
                      f"average p99 latency of {format_latency(min_p99)}, while {max_size}B records have "
                      f"the highest at {format_latency(max_p99)}. This represents a "
                      f"{(max_p99/min_p99 - 1)*100:.1f}% increase in latency.")
            
            insights.append(insight)
    
    # Insight 3: Impact of fill level on performance
    fill_levels = sorted(merged_df['target_pct'].unique())
    if len(fill_levels) > 1:
        p99_by_fill = merged_df.groupby('target_pct')['p99'].mean()
        tps_by_fill = merged_df.groupby('target_pct')['tps'].mean()
        
        if not p99_by_fill.isna().all() and not tps_by_fill.isna().all():
            min_fill_p99 = p99_by_fill.idxmin()
            max_fill_p99 = p99_by_fill.idxmax()
            min_fill_tps = tps_by_fill.idxmax()  # Higher TPS is better
            max_fill_tps = tps_by_fill.idxmin()  # Lower TPS is worse
            
            p99_increase = (p99_by_fill.max() / p99_by_fill.min() - 1) * 100
            tps_decrease = (1 - tps_by_fill.min() / tps_by_fill.max()) * 100
            
            insight = (f"Database fill level has a significant impact on write performance. "
                      f"At {min_fill_p99}% fill, p99 latency is lowest, while at {max_fill_p99}% fill, "
                      f"it increases by {p99_increase:.1f}%. Similarly, TPS is highest at {min_fill_tps}% fill "
                      f"and decreases by {tps_decrease:.1f}% at {max_fill_tps}% fill. This demonstrates "
                      f"the performance impact of database utilization on write operations.")
            
            insights.append(insight)
    
    # Insight 4: Latency distribution
    if not merged_df.empty and not merged_df['p50'].isna().all() and not merged_df['p99'].isna().all() and not merged_df['p99.9'].isna().all():
        p50_avg = merged_df['p50'].mean()
        p99_avg = merged_df['p99'].mean()
        p999_avg = merged_df['p99.9'].mean()
        
        if p50_avg > 0:  # Avoid division by zero
            p99_p50_ratio = p99_avg / p50_avg
            p999_p50_ratio = p999_avg / p50_avg
            
            if p99_p50_ratio > 5:
                insight = (f"Write latency shows significant variability. While average p50 latency is "
                          f"{format_latency(p50_avg)}, p99 latency is {p99_p50_ratio:.1f}x higher at "
                          f"{format_latency(p99_avg)}, and p99.9 latency is {p999_p50_ratio:.1f}x higher at "
                          f"{format_latency(p999_avg)}. This indicates occasional high-latency outliers "
                          f"that could impact application performance.")
            else:
                insight = (f"Write latency distribution is relatively consistent. The average p50 latency is "
                          f"{format_latency(p50_avg)}, with p99 latency at {format_latency(p99_avg)} "
                          f"({p99_p50_ratio:.1f}x higher) and p99.9 latency at {format_latency(p999_avg)} "
                          f"({p999_p50_ratio:.1f}x higher). This suggests stable write performance with "
                          f"few outliers.")
            
            insights.append(insight)
    
    # Insight 5: TPS vs Latency tradeoff
    if not merged_df.empty and not merged_df['tps'].isna().all() and not merged_df['p99'].isna().all():
        # Check if we have enough data points for correlation
        if len(merged_df) > 1:
            corr_matrix = merged_df[['tps', 'p99']].corr()
            if not corr_matrix.isna().all().all():  # Check if correlation matrix has valid values
                corr = corr_matrix.iloc[0, 1]
                
                if corr > 0.5:
                    insight = (f"There is a strong positive correlation ({corr:.2f}) between throughput and latency, "
                              f"indicating that configurations optimized for maximum TPS will likely experience "
                              f"higher latencies. Applications should balance throughput requirements with "
                              f"acceptable latency thresholds.")
                elif corr < -0.5:
                    insight = (f"There is a strong negative correlation ({corr:.2f}) between throughput and latency, "
                              f"suggesting that configurations with higher TPS actually experience lower latencies. "
                              f"This indicates that the system performs best when fully utilized.")
                else:
                    insight = (f"There is a weak correlation ({corr:.2f}) between throughput and latency, "
                              f"suggesting that it may be possible to optimize for both high throughput and "
                              f"low latency simultaneously with the right configuration.")
                
                insights.append(insight)
    
    return insights


def generate_recommendations(hdr_df, log_df, summary_stats, insights):
    """
    Generate recommendations from benchmark data and insights.
    
    Args:
        hdr_df: DataFrame containing HDR data
        log_df: DataFrame containing log data
        summary_stats: Dictionary containing summary statistics
        insights: List of insights
        
    Returns:
        list: List of recommendations
    """
    recommendations = []
    
    # Calculate average TPS for each configuration
    tps_avg = log_df.groupby(['record_size', 'target_pct', 'threads'])['tps'].mean().reset_index()
    
    # Merge with HDR data
    merged_df = pd.merge(
        hdr_df,
        tps_avg,
        on=['record_size', 'target_pct', 'threads'],
        how='inner'
    )
    
    # Recommendation 1: Optimal configuration for high throughput
    best_tps_config = summary_stats['best_tps_config']
    best_tps_row = merged_df[(merged_df['record_size'] == best_tps_config['record_size']) & 
                           (merged_df['target_pct'] == best_tps_config['target_pct']) & 
                           (merged_df['threads'] == best_tps_config['threads'])]
    
    if not best_tps_row.empty:
        p99_latency = best_tps_row['p99'].values[0]
        recommendation = (f"For maximum write throughput, use {best_tps_config['threads']} threads with "
                         f"{best_tps_config['record_size']}B records. This configuration achieves "
                         f"{best_tps_config['tps']:.0f} TPS with a p99 latency of {format_latency(p99_latency)}. "
                         f"Note that this configuration works best at {best_tps_config['target_pct']}% database fill level.")
        recommendations.append(recommendation)
    
    # Recommendation 2: Optimal configuration for low latency
    best_p99_config = summary_stats['best_latency_configs']['p99']
    best_p99_row = merged_df[(merged_df['record_size'] == best_p99_config['record_size']) & 
                           (merged_df['target_pct'] == best_p99_config['target_pct']) & 
                           (merged_df['threads'] == best_p99_config['threads'])]
    
    if not best_p99_row.empty:
        tps = best_p99_row['tps'].values[0]
        recommendation = (f"For lowest write latency, use {best_p99_config['threads']} threads with "
                         f"{best_p99_config['record_size']}B records. This configuration achieves "
                         f"a p99 latency of {format_latency(best_p99_config['latency'])} with {tps:.0f} TPS. "
                         f"This configuration works best at {best_p99_config['target_pct']}% database fill level.")
        recommendations.append(recommendation)
    
    # Recommendation 3: Balanced configuration
    # Find configurations with good TPS and latency
    if not merged_df.empty and not merged_df['tps'].isna().all() and not merged_df['p99'].isna().all():
        merged_df['tps_rank'] = merged_df['tps'].rank(ascending=False)
        merged_df['p99_rank'] = merged_df['p99'].rank(ascending=True)
        merged_df['combined_rank'] = merged_df['tps_rank'] + merged_df['p99_rank']
        
        if not merged_df['combined_rank'].isna().all():
            balanced_config = merged_df.loc[merged_df['combined_rank'].idxmin()]
            
            recommendation = (f"For a balanced write performance, use {balanced_config['threads']} threads with "
                             f"{balanced_config['record_size']}B records at {balanced_config['target_pct']}% fill level. "
                             f"This configuration achieves {balanced_config['tps']:.0f} TPS with a p99 latency of "
                             f"{format_latency(balanced_config['p99'])}.")
            recommendations.append(recommendation)
    
    # Recommendation 4: Database fill level management
    fill_levels = sorted(merged_df['target_pct'].unique())
    if len(fill_levels) > 1:
        p99_by_fill = merged_df.groupby('target_pct')['p99'].mean()
        tps_by_fill = merged_df.groupby('target_pct')['tps'].mean()
        
        if not p99_by_fill.isna().all():
            worst_fill = p99_by_fill.idxmax()
            best_fill = p99_by_fill.idxmin()
            
            p99_increase = (p99_by_fill.max() / p99_by_fill.min() - 1) * 100
            
            if p99_increase > 50:
                recommendation = (f"Database fill level significantly impacts write performance. Consider implementing "
                                 f"proactive data management policies to maintain fill levels below {worst_fill}%. "
                                 f"When possible, schedule bulk write operations during periods of low database "
                                 f"utilization. Performance degradation of over {p99_increase:.0f}% was observed "
                                 f"between {best_fill}% and {worst_fill}% fill levels.")
                recommendations.append(recommendation)
    
    # Recommendation 5: Record size optimization
    record_sizes = sorted(merged_df['record_size'].unique())
    if len(record_sizes) > 1:
        p99_by_size = merged_df.groupby('record_size')['p99'].mean()
        tps_by_size = merged_df.groupby('record_size')['tps'].mean()
        
        if not p99_by_size.isna().all() and not tps_by_size.isna().all():
            best_size_p99 = p99_by_size.idxmin()
            best_size_tps = tps_by_size.idxmax()
            
            if best_size_p99 == best_size_tps:
                recommendation = (f"The optimal record size for both throughput and latency is {best_size_p99}B. "
                                 f"When possible, structure your data to use this record size for write-intensive "
                                 f"operations.")
            else:
                recommendation = (f"Record size significantly impacts write performance. For latency-sensitive "
                                 f"operations, use {best_size_p99}B records. For throughput-oriented workloads, "
                                 f"use {best_size_tps}B records. Consider splitting large records or batching "
                                 f"small records to optimize performance based on your application's requirements.")
            
            recommendations.append(recommendation)
    
    # Recommendation 6: Thread count optimization
    thread_counts = sorted(merged_df['threads'].unique())
    if len(thread_counts) > 1:
        tps_by_thread = merged_df.groupby('threads')['tps'].mean()
        p99_by_thread = merged_df.groupby('threads')['p99'].mean()
        
        if not tps_by_thread.isna().all() and not p99_by_thread.isna().all():
            best_thread_tps = tps_by_thread.idxmax()
            best_thread_p99 = p99_by_thread.idxmin()
            
            if best_thread_tps == best_thread_p99:
                recommendation = (f"The optimal thread count for both throughput and latency is {best_thread_tps}. "
                                 f"Configure your client applications to use this level of concurrency for "
                                 f"write operations.")
            else:
                recommendation = (f"Thread count optimization depends on your performance goals. For maximum "
                                 f"throughput, use {best_thread_tps} threads. For lowest latency, use "
                                 f"{best_thread_p99} threads. Consider implementing adaptive concurrency "
                                 f"control based on current system load and performance requirements.")
            
            recommendations.append(recommendation)
    
    return recommendations


def create_summary_tables(hdr_df, log_df):
    """
    Create summary tables for the report.
    
    Args:
        hdr_df: DataFrame containing HDR data
        log_df: DataFrame containing log data
        
    Returns:
        dict: Dictionary containing summary tables
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
    
    # Table 1: Performance by thread count
    thread_table = merged_df.groupby('threads').agg({
        'tps': 'mean',
        'p50': 'mean',
        'p99': 'mean',
        'p99.9': 'mean'
    }).reset_index()
    
    thread_table = thread_table.sort_values('threads')
    thread_table = thread_table.round({'tps': 0, 'p50': 0, 'p99': 0, 'p99.9': 0})
    thread_table_html = thread_table.to_html(index=False, classes='table table-striped')
    
    # Table 2: Performance by record size
    size_table = merged_df.groupby('record_size').agg({
        'tps': 'mean',
        'p50': 'mean',
        'p99': 'mean',
        'p99.9': 'mean'
    }).reset_index()
    
    size_table = size_table.sort_values('record_size')
    size_table = size_table.round({'tps': 0, 'p50': 0, 'p99': 0, 'p99.9': 0})
    size_table_html = size_table.to_html(index=False, classes='table table-striped')
    
    # Table 3: Performance by fill level
    fill_table = merged_df.groupby('target_pct').agg({
        'tps': 'mean',
        'p50': 'mean',
        'p99': 'mean',
        'p99.9': 'mean'
    }).reset_index()
    
    fill_table = fill_table.sort_values('target_pct')
    fill_table = fill_table.round({'tps': 0, 'p50': 0, 'p99': 0, 'p99.9': 0})
    fill_table_html = fill_table.to_html(index=False, classes='table table-striped')
    
    # Table 4: Top 5 configurations by TPS
    top_tps_table = merged_df.sort_values('tps', ascending=False).head(5)
    top_tps_table = top_tps_table[['record_size', 'target_pct', 'threads', 'tps', 'p50', 'p99', 'p99.9']]
    top_tps_table = top_tps_table.round({'tps': 0, 'p50': 0, 'p99': 0, 'p99.9': 0})
    top_tps_table_html = top_tps_table.to_html(index=False, classes='table table-striped')
    
    # Table 5: Top 5 configurations by p99 latency
    top_p99_table = merged_df.sort_values('p99').head(5)
    top_p99_table = top_p99_table[['record_size', 'target_pct', 'threads', 'tps', 'p50', 'p99', 'p99.9']]
    top_p99_table = top_p99_table.round({'tps': 0, 'p50': 0, 'p99': 0, 'p99.9': 0})
    top_p99_table_html = top_p99_table.to_html(index=False, classes='table table-striped')
    
    return {
        'thread_table': thread_table_html,
        'size_table': size_table_html,
        'fill_table': fill_table_html,
        'top_tps_table': top_tps_table_html,
        'top_p99_table': top_p99_table_html
    }


def create_html_template():
    """
    Create HTML template for the report.
    
    Returns:
        str: HTML template
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Aerospike Write Benchmark Report</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1, h2, h3 {
                color: #2c3e50;
                margin-top: 30px;
            }
            h1 {
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            .summary-box {
                background-color: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin: 20px 0;
            }
            .insight-box {
                background-color: #f0f7fb;
                border-left: 4px solid #5bc0de;
                padding: 15px;
                margin: 15px 0;
            }
            .recommendation-box {
                background-color: #eafaf1;
                border-left: 4px solid #2ecc71;
                padding: 15px;
                margin: 15px 0;
            }
            .visualization {
                margin: 30px 0;
                text-align: center;
            }
            .visualization img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .table {
                margin: 20px 0;
            }
            .table th {
                background-color: #f2f2f2;
            }
            footer {
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                text-align: center;
                font-size: 0.9em;
                color: #777;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Aerospike Write Benchmark Analysis Report</h1>
            <p class="lead">Generated on {{ generation_date }}</p>
            
            <h2>Executive Summary</h2>
            <div class="summary-box">
                <p>This report analyzes write performance benchmarks for Aerospike, examining the impact of various configurations on throughput and latency. The analysis covers {{ summary_stats.overall_stats.total_configs }} different configurations, varying record sizes ({{ summary_stats.overall_stats.record_sizes|join(', ') }}B), thread counts ({{ summary_stats.overall_stats.thread_counts|join(', ') }}), and database fill levels ({{ summary_stats.overall_stats.fill_levels|join(', ') }}%).</p>
                
                <p>Key findings:</p>
                <ul>
                    <li>Maximum throughput: <strong>{{ "%.0f"|format(summary_stats.overall_stats.max_tps) }} TPS</strong> (achieved with {{ summary_stats.best_tps_config.record_size }}B records, {{ summary_stats.best_tps_config.threads }} threads, at {{ summary_stats.best_tps_config.target_pct }}% fill)</li>
                    <li>Best p99 latency: <strong>{{ format_latency(summary_stats.overall_stats.min_p99) }}</strong> (achieved with {{ summary_stats.best_latency_configs.p99.record_size }}B records, {{ summary_stats.best_latency_configs.p99.threads }} threads, at {{ summary_stats.best_latency_configs.p99.target_pct }}% fill)</li>
                    <li>Average p50/p99/p99.9 latencies across all configurations: {{ format_latency(summary_stats.overall_stats.avg_p50) }} / {{ format_latency(summary_stats.overall_stats.avg_p99) }} / {{ format_latency(summary_stats.overall_stats.avg_p99_9) }}</li>
                </ul>
            </div>
            
            <h2>Key Insights</h2>
            {% for insight in insights %}
            <div class="insight-box">
                <p>{{ insight }}</p>
            </div>
            {% endfor %}
            
            <h2>Recommendations</h2>
            {% for recommendation in recommendations %}
            <div class="recommendation-box">
                <p>{{ recommendation }}</p>
            </div>
            {% endfor %}
            
            <h2>Performance Summary Tables</h2>
            
            <h3>Performance by Thread Count</h3>
            {{ tables.thread_table|safe }}
            
            <h3>Performance by Record Size</h3>
            {{ tables.size_table|safe }}
            
            <h3>Performance by Fill Level</h3>
            {{ tables.fill_table|safe }}
            
            <h3>Top 5 Configurations by TPS</h3>
            {{ tables.top_tps_table|safe }}
            
            <h3>Top 5 Configurations by p99 Latency</h3>
            {{ tables.top_p99_table|safe }}
            
            <h2>Visualizations</h2>
            
            <h3>Latency Percentiles by Thread Count</h3>
            <div class="visualization">
                {% for record_size in summary_stats.overall_stats.record_sizes %}
                {% for target_pct in summary_stats.overall_stats.fill_levels %}
                <div>
                    <h4>Record Size: {{ record_size }}B, Fill Level: {{ target_pct }}%</h4>
                    <img src="visualizations/latency_percentiles_by_thread_count_{{ record_size }}B_{{ target_pct }}pct.png" alt="Latency Percentiles by Thread Count">
                </div>
                {% endfor %}
                {% endfor %}
            </div>
            
            <h3>TPS by Thread Count</h3>
            <div class="visualization">
                {% for record_size in summary_stats.overall_stats.record_sizes %}
                <div>
                    <h4>Record Size: {{ record_size }}B</h4>
                    <img src="visualizations/tps_by_thread_count_{{ record_size }}B.png" alt="TPS by Thread Count">
                </div>
                {% endfor %}
            </div>
            
            <h3>Latency Heatmaps</h3>
            <div class="visualization">
                {% for target_pct in summary_stats.overall_stats.fill_levels %}
                <div>
                    <h4>Fill Level: {{ target_pct }}%</h4>
                    <img src="visualizations/latency_heatmap_p99_{{ target_pct }}pct.png" alt="p99 Latency Heatmap">
                </div>
                {% endfor %}
            </div>
            
            <h3>TPS vs p99 Latency</h3>
            <div class="visualization">
                {% for record_size in summary_stats.overall_stats.record_sizes %}
                <div>
                    <h4>Record Size: {{ record_size }}B</h4>
                    <img src="visualizations/tps_vs_p99_{{ record_size }}B.png" alt="TPS vs p99 Latency">
                </div>
                {% endfor %}
            </div>
            
            <h3>Impact of Fill Level</h3>
            <div class="visualization">
                {% for record_size in summary_stats.overall_stats.record_sizes %}
                <div>
                    <h4>Record Size: {{ record_size }}B</h4>
                    <img src="visualizations/fill_level_impact_p99_{{ record_size }}B.png" alt="Impact of Fill Level on p99 Latency">
                </div>
                {% endfor %}
            </div>
            
            <footer>
                <p>Generated by Aerospike Write Benchmark Analysis Tool</p>
                <p>{{ generation_date }}</p>
            </footer>
        </div>
    </body>
    </html>
    """


def generate_report(benchmark_data, output_dir, report_file, viz_dir, open_report=False):
    """
    Generate HTML report from benchmark data and visualizations.
    
    Args:
        benchmark_data: Dictionary containing benchmark data
        output_dir: Directory for output files
        report_file: Output HTML report file name
        viz_dir: Directory for visualizations
        open_report: Whether to open the report in the default browser
    """
    # Create DataFrames
    hdr_df, log_df = create_dataframes(benchmark_data)
    
    # Generate summary statistics
    summary_stats = generate_summary_statistics(hdr_df, log_df)
    
    # Generate insights
    insights = generate_insights(hdr_df, log_df, summary_stats)
    
    # Generate recommendations
    recommendations = generate_recommendations(hdr_df, log_df, summary_stats, insights)
    
    # Create summary tables
    tables = create_summary_tables(hdr_df, log_df)
    
    # Create HTML template
    template_str = create_html_template()
    
    # Render template
    template = Environment(loader=FileSystemLoader(searchpath=".")).from_string(template_str)
    html = template.render(
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary_stats=summary_stats,
        insights=insights,
        recommendations=recommendations,
        tables=tables,
        format_latency=format_latency
    )
    
    # Save HTML report
    report_path = os.path.join(output_dir, report_file)
    with open(report_path, 'w') as f:
        f.write(html)
    
    print(f"Generated HTML report: {report_path}")
    
    # Open report in browser if requested
    if open_report:
        webbrowser.open(f"file://{os.path.abspath(report_path)}")


def main():
    """Main function to generate benchmark report."""
    parser = argparse.ArgumentParser(description='Generate Aerospike write benchmark report')
    parser.add_argument('--data-dir', default='benchmark_analysis', help='Directory containing benchmark data')
    parser.add_argument('--output-dir', default='benchmark_analysis', help='Directory for output files')
    parser.add_argument('--json-file', default='benchmark_data.json', help='Input JSON file name')
    parser.add_argument('--report-file', default='benchmark_report.html', help='Output HTML report file name')
    parser.add_argument('--viz-dir', default='visualizations', help='Directory for visualizations')
    parser.add_argument('--open-report', action='store_true', help='Open the HTML report in the default browser')
    args = parser.parse_args()
    
    # Load benchmark data
    json_path = os.path.join(args.data_dir, args.json_file)
    benchmark_data = load_benchmark_data(json_path)
    
    # Generate report
    generate_report(benchmark_data, args.output_dir, args.report_file, args.viz_dir, args.open_report)


if __name__ == '__main__':
    main()
