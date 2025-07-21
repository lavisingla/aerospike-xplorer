import re
import sys

def count_frequency_deviations(file_path, abs_threshold, pct_threshold):
    pattern = r'existingFrequency (\d+), expectedFrequency (\d+)'
    count = 0
    total_lines = 0
    deviating_entries = []
    all_keys = {}
    with open(file_path, 'r') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                total_lines += 1
                existing_freq = int(match.group(1))
                expected_freq = int(match.group(2))
                
                # Calculate absolute difference
                abs_diff = abs(existing_freq - expected_freq)
                
                # Calculate percentage deviation
                if expected_freq != 0:  # Avoid division by zero
                    pct_diff = (abs_diff / expected_freq) * 100
                else:
                    pct_diff = float('inf')  # Handle division by zero
                
                # Check if either threshold is exceeded
                if abs_diff > abs_threshold and pct_diff > pct_threshold:
                    count += 1
                    # Extract config key for reporting
                    key_match = re.search(r'for (configKey\w+),', line)
                    config_key = key_match.group(1) if key_match else "unknown"
                    
                    if config_key not in all_keys:
                        deviating_entries.append({
                            'key': config_key,
                            'existing': existing_freq,
                            'expected': expected_freq,
                            'abs_diff': abs_diff,
                            'pct_diff': pct_diff
                        })
                        all_keys[config_key] = True
    
    return count, total_lines, deviating_entries

def main():
    # if len(sys.argv) < 4:
    #     print("Usage: python script.py <log_file_path> <abs_threshold> <pct_threshold>")
    #     print("Example: python script.py logs2.txt 100 20")
    #     print("  This will find entries where absolute difference > 100 OR percentage deviation > 20%")
    #     sys.exit(1)
    
    file_path = 'logs2.txt'
    abs_threshold = 20
    pct_threshold = 10.0
    
    count, total, deviating_entries = count_frequency_deviations(file_path, abs_threshold, pct_threshold)
    
    print(f"Total log entries: {total}")
    print(f"Entries with abs diff > {abs_threshold} OR pct diff > {pct_threshold}%: {count}")
    print(f"Percentage of total: {(count/total)*100:.2f}%")
    
    # Sort by percentage difference for reporting
    if deviating_entries:
        print("\nTop 100 deviating entries (by percentage):")
        sorted_entries = sorted(deviating_entries, key=lambda x: x['pct_diff'], reverse=True)
        for i, entry in enumerate(sorted_entries[:100]):
            print(f"{i+1}. {entry['key']}: existing={entry['existing']}, expected={entry['expected']}, " 
                  f"diff={entry['abs_diff']}, deviation={entry['pct_diff']:.2f}%")

if __name__ == "__main__":
    main()
