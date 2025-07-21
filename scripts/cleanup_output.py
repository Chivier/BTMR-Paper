#!/usr/bin/env python3
"""
Output Cleanup Script

This script provides utilities for managing and cleaning up the output directory.
It can remove old outputs, compress files, and maintain the metadata CSV.
"""
import os
import sys
import shutil
import argparse
from datetime import datetime, timedelta
import csv
from typing import List, Dict

# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metadata_logger import MetadataLogger


class OutputCleaner:
    """
    Handles cleanup operations for the output directory.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the output cleaner.
        
        Args:
            output_dir: Path to the output directory
        """
        self.output_dir = output_dir
        self.logger = MetadataLogger(output_dir)
        self.csv_path = self.logger.csv_path
    
    def cleanup_old_outputs(self, days: int = 7, dry_run: bool = True) -> List[str]:
        """
        Remove output directories older than specified days.
        
        Args:
            days: Remove directories older than this many days
            dry_run: If True, only show what would be deleted
            
        Returns:
            List of removed directories
        """
        removed_dirs = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get all paper directories
        for item in os.listdir(self.output_dir):
            if item.startswith("paper_") and os.path.isdir(os.path.join(self.output_dir, item)):
                dir_path = os.path.join(self.output_dir, item)
                
                # Extract timestamp from directory name
                try:
                    # Format: paper_YYYYMMDD_HHMMSS
                    timestamp_str = item.replace("paper_", "")
                    dir_timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if dir_timestamp < cutoff_date:
                        if dry_run:
                            print(f"Would remove: {dir_path} (created: {dir_timestamp})")
                        else:
                            shutil.rmtree(dir_path)
                            print(f"Removed: {dir_path}")
                        removed_dirs.append(dir_path)
                except Exception as e:
                    print(f"Error processing {item}: {e}")
        
        return removed_dirs
    
    def cleanup_by_size(self, max_size_mb: float = 1000, dry_run: bool = True) -> List[str]:
        """
        Remove oldest outputs to keep total size under limit.
        
        Args:
            max_size_mb: Maximum total size in megabytes
            dry_run: If True, only show what would be deleted
            
        Returns:
            List of removed directories
        """
        # Get all directories with their sizes and timestamps
        dir_info = []
        total_size = 0
        
        for item in os.listdir(self.output_dir):
            if item.startswith("paper_") and os.path.isdir(os.path.join(self.output_dir, item)):
                dir_path = os.path.join(self.output_dir, item)
                
                # Calculate directory size
                dir_size = self._get_dir_size(dir_path)
                total_size += dir_size
                
                # Get timestamp
                try:
                    timestamp_str = item.replace("paper_", "")
                    dir_timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    dir_info.append({
                        'path': dir_path,
                        'size': dir_size,
                        'timestamp': dir_timestamp,
                        'name': item
                    })
                except:
                    pass
        
        # Sort by timestamp (oldest first)
        dir_info.sort(key=lambda x: x['timestamp'])
        
        removed_dirs = []
        current_size = total_size / (1024 * 1024)  # Convert to MB
        
        print(f"Current total size: {current_size:.2f} MB")
        
        # Remove oldest directories until under limit
        for info in dir_info:
            if current_size <= max_size_mb:
                break
            
            if dry_run:
                print(f"Would remove: {info['path']} ({info['size'] / (1024 * 1024):.2f} MB)")
            else:
                shutil.rmtree(info['path'])
                print(f"Removed: {info['path']} ({info['size'] / (1024 * 1024):.2f} MB)")
            
            removed_dirs.append(info['path'])
            current_size -= info['size'] / (1024 * 1024)
        
        print(f"Final size: {current_size:.2f} MB")
        return removed_dirs
    
    def cleanup_orphaned_entries(self, dry_run: bool = True):
        """
        Remove CSV entries for outputs that no longer exist.
        
        Args:
            dry_run: If True, only show what would be removed
        """
        if not os.path.exists(self.csv_path):
            print("No metadata CSV found.")
            return
        
        # Read all entries
        valid_entries = []
        removed_count = 0
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            entries = list(reader)
        
        for entry in entries:
            output_path = entry.get('output_path', '')
            
            # Check if the output file still exists
            if os.path.exists(output_path):
                valid_entries.append(entry)
            else:
                removed_count += 1
                if dry_run:
                    print(f"Would remove CSV entry: {entry.get('title', 'Unknown')} - {output_path}")
                else:
                    print(f"Removed CSV entry: {entry.get('title', 'Unknown')}")
        
        # Write back valid entries
        if not dry_run and removed_count > 0:
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.logger.fieldnames)
                writer.writeheader()
                writer.writerows(valid_entries)
        
        print(f"\nTotal entries removed: {removed_count}")
    
    def show_statistics(self):
        """Display statistics about the output directory."""
        stats = self.logger.get_statistics()
        
        print("\n=== Output Directory Statistics ===")
        print(f"Total papers processed: {stats['total_papers']}")
        print(f"Total figures extracted: {stats['total_figures']}")
        print(f"Total tables extracted: {stats['total_tables']}")
        print(f"Average processing time: {stats['avg_processing_time']:.2f} seconds")
        print(f"Total storage used: {stats['total_size_mb']:.2f} MB")
        
        print("\nOutput formats:")
        for fmt, count in stats.get('formats_used', {}).items():
            print(f"  {fmt}: {count}")
        
        print("\nLanguages:")
        for lang, count in stats.get('languages', {}).items():
            print(f"  {lang}: {count}")
    
    def _get_dir_size(self, path: str) -> int:
        """Get total size of a directory in bytes."""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total += os.path.getsize(filepath)
        return total


def main():
    """Main function for the cleanup script."""
    parser = argparse.ArgumentParser(
        description="Clean up BTMR output directory"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Cleanup by age
    age_parser = subparsers.add_parser('age', help='Remove outputs older than N days')
    age_parser.add_argument('days', type=int, help='Remove outputs older than this many days')
    age_parser.add_argument('--execute', action='store_true', help='Actually remove files (default is dry run)')
    
    # Cleanup by size
    size_parser = subparsers.add_parser('size', help='Keep total size under limit')
    size_parser.add_argument('max_mb', type=float, help='Maximum total size in MB')
    size_parser.add_argument('--execute', action='store_true', help='Actually remove files (default is dry run)')
    
    # Cleanup orphaned entries
    orphan_parser = subparsers.add_parser('orphans', help='Remove CSV entries for missing files')
    orphan_parser.add_argument('--execute', action='store_true', help='Actually update CSV (default is dry run)')
    
    # Show statistics
    stats_parser = subparsers.add_parser('stats', help='Show output directory statistics')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize cleaner
    cleaner = OutputCleaner()
    
    # Execute command
    if args.command == 'age':
        print(f"Cleaning outputs older than {args.days} days...")
        removed = cleaner.cleanup_old_outputs(days=args.days, dry_run=not args.execute)
        print(f"\nTotal directories {'would be' if not args.execute else ''} removed: {len(removed)}")
        if not args.execute:
            print("\nUse --execute to actually remove files")
    
    elif args.command == 'size':
        print(f"Cleaning to keep size under {args.max_mb} MB...")
        removed = cleaner.cleanup_by_size(max_size_mb=args.max_mb, dry_run=not args.execute)
        print(f"\nTotal directories {'would be' if not args.execute else ''} removed: {len(removed)}")
        if not args.execute:
            print("\nUse --execute to actually remove files")
    
    elif args.command == 'orphans':
        print("Cleaning orphaned CSV entries...")
        cleaner.cleanup_orphaned_entries(dry_run=not args.execute)
        if not args.execute:
            print("\nUse --execute to actually update the CSV")
    
    elif args.command == 'stats':
        cleaner.show_statistics()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()