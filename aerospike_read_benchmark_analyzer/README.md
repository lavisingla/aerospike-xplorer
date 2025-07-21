# Aerospike Read Benchmark Analysis Tools

This repository contains a set of tools for analyzing Aerospike read benchmark data. The tools extract data from benchmark log files, generate visualizations, and create a comprehensive HTML report with insights and recommendations.

## Overview

The benchmark analysis pipeline consists of the following components:

1. **Data Extraction**: Parses HDR histogram files and read latency log files to extract key metrics.
2. **Visualization**: Generates various charts and graphs to visualize the benchmark results.
3. **Report Generation**: Creates a comprehensive HTML report with summary statistics, insights, and recommendations.
4. **Analysis Pipeline**: Orchestrates the entire analysis process from data extraction to report generation.

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - jinja2

You can install the required packages using pip:

```bash
pip install pandas numpy matplotlib seaborn jinja2
```

## Directory Structure

The benchmark data should be organized as follows:

```
aerospike_read_benchmark_stats/
├── hdr_stats/                  # HDR histogram files
│   ├── read_latency_*.txt      # HDR histogram data
│   └── ...
└── read_latency_results/       # Read latency log files
    ├── read_latency_*.log      # Benchmark log data
    └── ...
```

## Usage

### Running the Complete Analysis

The simplest way to run the complete analysis is to use the `analyze_benchmark.py` script:

```bash
python analyze_benchmark.py [options]
```

#### Options

- `--data-dir DIR`: Directory containing benchmark data (default: current directory)
- `--output-dir DIR`: Directory for output files (default: 'benchmark_analysis')
- `--json-file FILE`: Output JSON file name (default: 'benchmark_data.json')
- `--csv-file FILE`: Output CSV file name (default: 'benchmark_summary.csv')
- `--viz-dir DIR`: Directory for visualizations (default: 'visualizations')
- `--report-file FILE`: Output HTML report file name (default: 'benchmark_report.html')
- `--open-report`: Open the HTML report in the default browser after generation

#### Example

```bash
python analyze_benchmark.py --data-dir /path/to/benchmark/data --output-dir results --open-report
```

### Running Individual Components

You can also run each component of the analysis pipeline separately:

#### Data Extraction

```bash
python extract_benchmark_data.py
```

This script extracts data from the benchmark files and saves it to:
- `benchmark_data.json`: Complete benchmark data in JSON format
- `benchmark_summary.csv`: Summary statistics in CSV format

#### Visualization

```bash
python visualize_benchmark_data.py
```

This script generates various visualizations and saves them to the `visualizations` directory.

#### Report Generation

```bash
python generate_benchmark_report.py
```

This script generates a comprehensive HTML report (`benchmark_report.html`) from the extracted data and visualizations.

## Output Files

The analysis pipeline generates the following output files:

- `benchmark_data.json`: Complete benchmark data in JSON format
- `benchmark_summary.csv`: Summary statistics in CSV format
- `visualizations/*.png`: Various charts and graphs visualizing the benchmark results
- `benchmark_report.html`: Comprehensive HTML report with summary statistics, insights, and recommendations

## Understanding the Benchmark Data

The benchmark data consists of two main types of files:

### HDR Histogram Files

These files contain detailed latency distribution data for each benchmark configuration. The filename format is:

```
read_latency_<percentage>pct_<size>B_thr<threads>_<timestamp>.txt
```

Where:
- `<percentage>`: Storage utilization percentage (25, 50, 75)
- `<size>`: Record size in bytes (8192, 16384, 32768, 65536, 131072)
- `<threads>`: Number of client threads (1, 25, 50, 100, 200)
- `<timestamp>`: Timestamp when the benchmark was run

### Read Latency Log Files

These files contain per-second performance metrics for each benchmark configuration. The filename format is:

```
read_latency_<percentage>pct_<size>B_thr<threads>_<timestamp>.log
```

With the same parameters as the HDR histogram files.

## Analysis Insights

The analysis provides insights into:

1. **Impact of Thread Count**: How different thread counts affect throughput and latency
2. **Impact of Record Size**: How different record sizes affect throughput and latency
3. **Impact of Storage Utilization**: How different storage utilization levels affect throughput and latency
4. **Optimal Configurations**: Recommended configurations for different use cases

## Example Report

The HTML report includes:

- Executive summary with key statistics
- Key insights derived from the benchmark data
- Recommendations for optimal configurations
- Summary tables showing performance metrics across different configurations
- Various visualizations including:
  - Latency percentiles by thread count
  - TPS by thread count
  - Latency by record size
  - Latency and TPS heatmaps
  - Latency distribution curves
  - TPS and latency over time
  - Comparative analysis charts

## License

This project is licensed under the MIT License - see the LICENSE file for details.
