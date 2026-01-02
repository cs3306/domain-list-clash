#!/usr/bin/env python3
"""
Convert v2fly/domain-list-community data files to Clash-compatible YAML rules.

Conversion mapping:
- domain:xxx.com or xxx.com -> DOMAIN-SUFFIX,xxx.com
- full:xxx.com -> DOMAIN,xxx.com
- keyword:xxx -> DOMAIN-KEYWORD,xxx
- regexp:xxx -> skipped (not supported by Clash)
- include:xxx -> recursively include the file
"""

import os
import re
import yaml
import shutil
import argparse
from pathlib import Path
from typing import Set, List, Dict
from datetime import datetime, timezone

# Repository URL
REPO_URL = "https://github.com/v2fly/domain-list-community"
DATA_DIR = "domain-list-community/data"
OUTPUT_DIR = "output"


def clone_or_update_repo():
    """Clone or update the domain-list-community repository."""
    if os.path.exists("domain-list-community"):
        print("Updating domain-list-community repository...")
        os.system("cd domain-list-community && git pull --quiet")
    else:
        print("Cloning domain-list-community repository...")
        os.system(f"git clone --depth 1 --quiet {REPO_URL}")


def parse_line(line: str) -> tuple:
    """
    Parse a single line from domain-list-community data file.
    
    Returns:
        tuple: (type, value, attributes) or (None, None, None) for invalid lines
    """
    # Remove comments
    if '#' in line:
        line = line.split('#')[0]
    
    line = line.strip()
    if not line:
        return None, None, None
    
    # Extract attributes (@attr1 @attr2)
    attributes = []
    attr_match = re.findall(r'@(\S+)', line)
    if attr_match:
        attributes = attr_match
        line = re.sub(r'\s*@\S+', '', line).strip()
    
    # Parse rule type
    if line.startswith('include:'):
        return 'include', line[8:].strip(), attributes
    elif line.startswith('full:'):
        return 'full', line[5:].strip(), attributes
    elif line.startswith('keyword:'):
        return 'keyword', line[8:].strip(), attributes
    elif line.startswith('regexp:'):
        return 'regexp', line[7:].strip(), attributes
    elif line.startswith('domain:'):
        return 'domain', line[7:].strip(), attributes
    else:
        # Default is domain (subdomain matching)
        return 'domain', line, attributes


def load_file(filepath: str, processed_files: Set[str] = None) -> List[Dict]:
    """
    Load and parse a domain-list-community data file.
    
    Args:
        filepath: Path to the data file
        processed_files: Set of already processed files (to avoid infinite loops)
    
    Returns:
        List of parsed rules with their types and values
    """
    if processed_files is None:
        processed_files = set()
    
    # Prevent infinite recursion
    abs_path = os.path.abspath(filepath)
    if abs_path in processed_files:
        return []
    processed_files.add(abs_path)
    
    rules = []
    
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return rules
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            rule_type, value, attrs = parse_line(line)
            
            if rule_type is None:
                continue
            
            if rule_type == 'include':
                # Recursively include another file
                include_path = os.path.join(os.path.dirname(filepath), value)
                rules.extend(load_file(include_path, processed_files))
            else:
                rules.append({
                    'type': rule_type,
                    'value': value,
                    'attributes': attrs
                })
    
    return rules


def convert_to_clash_rules(rules: List[Dict], with_policy: bool = False, policy: str = "PROXY") -> List[str]:
    """
    Convert parsed rules to Clash format.
    
    Args:
        rules: List of parsed rules
        with_policy: Whether to append policy to rules
        policy: The policy to use (e.g., PROXY, DIRECT, REJECT)
    
    Returns:
        List of Clash rule strings
    """
    clash_rules = []
    seen = set()  # Deduplicate
    
    for rule in rules:
        rule_type = rule['type']
        value = rule['value']
        
        if rule_type == 'domain':
            clash_rule = f"DOMAIN-SUFFIX,{value}"
        elif rule_type == 'full':
            clash_rule = f"DOMAIN,{value}"
        elif rule_type == 'keyword':
            clash_rule = f"DOMAIN-KEYWORD,{value}"
        elif rule_type == 'regexp':
            # Skip regexp rules as Clash doesn't support them natively
            continue
        else:
            continue
        
        if with_policy:
            clash_rule = f"{clash_rule},{policy}"
        
        if clash_rule not in seen:
            seen.add(clash_rule)
            clash_rules.append(clash_rule)
    
    return clash_rules


def save_yaml(rules: List[str], output_path: str, list_name: str):
    """Save rules as Clash-compatible YAML file."""
    # Create the YAML structure for rule-provider format
    data = {
        'payload': rules
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Generated from v2fly/domain-list-community\n")
        f.write(f"# Source: {list_name}\n")
        f.write(f"# Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total rules: {len(rules)}\n\n")
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def save_text(rules: List[str], output_path: str, list_name: str):
    """Save rules as plain text file (one rule per line)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Generated from v2fly/domain-list-community\n")
        f.write(f"# Source: {list_name}\n")
        f.write(f"# Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total rules: {len(rules)}\n\n")
        for rule in rules:
            f.write(f"{rule}\n")


def save_domain_only(rules: List[Dict], output_path: str, list_name: str):
    """Save as simple domain list (for behavior: domain rule providers)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    domains = []
    seen = set()
    
    for rule in rules:
        rule_type = rule['type']
        value = rule['value']
        
        if rule_type in ('domain', 'full'):
            # For domain behavior, use prefix format
            if rule_type == 'domain':
                domain = f"+.{value}"  # Subdomain matching
            else:
                domain = value  # Exact match
            
            if domain not in seen:
                seen.add(domain)
                domains.append(domain)
    
    data = {'payload': domains}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Generated from v2fly/domain-list-community\n")
        f.write(f"# Source: {list_name}\n")
        f.write(f"# Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"# Total domains: {len(domains)}\n")
        f.write(f"# Format: domain behavior (use with behavior: domain)\n\n")
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_all_data_files(data_dir: str) -> List[str]:
    """Get all data files from the repository."""
    files = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isfile(item_path) and not item.startswith('.'):
            files.append(item)
    return sorted(files)


def process_single_file(filename: str, data_dir: str, output_dir: str):
    """Process a single data file and generate outputs."""
    filepath = os.path.join(data_dir, filename)
    
    # Parse the file
    rules = load_file(filepath)
    
    if not rules:
        print(f"  Skipping {filename} (no valid rules)")
        return
    
    # Convert to Clash rules (classical format)
    clash_rules = convert_to_clash_rules(rules)
    
    if clash_rules:
        # Save as YAML (classical behavior)
        yaml_path = os.path.join(output_dir, "classical", f"{filename}.yaml")
        save_yaml(clash_rules, yaml_path, filename)
        
        # Save as text
        txt_path = os.path.join(output_dir, "classical", f"{filename}.txt")
        save_text(clash_rules, txt_path, filename)
    
    # Save domain-only format
    domain_path = os.path.join(output_dir, "domain", f"{filename}.yaml")
    save_domain_only(rules, domain_path, filename)
    
    print(f"  Processed {filename}: {len(clash_rules)} rules")


def generate_index(output_dir: str, files: List[str]):
    """Generate an index file listing all available rule sets."""
    index = {
        'name': 'domain-list-clash',
        'description': 'Clash rules converted from v2fly/domain-list-community',
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'total_files': len(files),
        'files': files
    }
    
    index_path = os.path.join(output_dir, "index.json")
    import json
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    # Also generate a README for the output directory
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("# Clash Rules from domain-list-community\n\n")
        f.write("这些规则文件由 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) 自动转换生成。\n\n")
        f.write(f"**最后更新**: {index['updated']}\n\n")
        f.write("## 使用方法\n\n")
        f.write("### Classical 格式 (behavior: classical)\n\n")
        f.write("```yaml\nrule-providers:\n")
        f.write("  google:\n")
        f.write("    type: http\n")
        f.write("    behavior: classical\n")
        f.write("    url: \"https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/classical/google.yaml\"\n")
        f.write("    path: ./ruleset/google.yaml\n")
        f.write("    interval: 86400\n\n")
        f.write("rules:\n")
        f.write("  - RULE-SET,google,PROXY\n")
        f.write("```\n\n")
        f.write("### Domain 格式 (behavior: domain)\n\n")
        f.write("```yaml\nrule-providers:\n")
        f.write("  google:\n")
        f.write("    type: http\n")
        f.write("    behavior: domain\n")
        f.write("    url: \"https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/domain/google.yaml\"\n")
        f.write("    path: ./ruleset/google.yaml\n")
        f.write("    interval: 86400\n\n")
        f.write("rules:\n")
        f.write("  - RULE-SET,google,PROXY\n")
        f.write("```\n\n")
        f.write("## 可用规则列表\n\n")
        f.write("| 名称 | Classical | Domain |\n")
        f.write("|------|-----------|--------|\n")
        for file in files[:50]:  # Only show first 50
            f.write(f"| {file} | [yaml](classical/{file}.yaml) | [yaml](domain/{file}.yaml) |\n")
        if len(files) > 50:
            f.write(f"\n... 共 {len(files)} 个规则文件\n")


def main():
    parser = argparse.ArgumentParser(description='Convert domain-list-community to Clash rules')
    parser.add_argument('--files', nargs='*', help='Specific files to convert (default: all)')
    parser.add_argument('--output', default=OUTPUT_DIR, help='Output directory')
    parser.add_argument('--skip-clone', action='store_true', help='Skip cloning/updating repo')
    args = parser.parse_args()
    
    # Clone or update repository
    if not args.skip_clone:
        clone_or_update_repo()
    
    # Get list of files to process
    if args.files:
        files = args.files
    else:
        files = get_all_data_files(DATA_DIR)
    
    print(f"Processing {len(files)} files...")
    
    # Clean output directory
    if os.path.exists(args.output):
        shutil.rmtree(args.output)
    os.makedirs(args.output)
    os.makedirs(os.path.join(args.output, "classical"))
    os.makedirs(os.path.join(args.output, "domain"))
    
    # Process each file
    processed_files = []
    for filename in files:
        process_single_file(filename, DATA_DIR, args.output)
        processed_files.append(filename)
    
    # Generate index
    generate_index(args.output, processed_files)
    
    print(f"\nDone! Output saved to {args.output}/")
    print(f"  - Classical format: {args.output}/classical/")
    print(f"  - Domain format: {args.output}/domain/")


if __name__ == '__main__':
    main()
