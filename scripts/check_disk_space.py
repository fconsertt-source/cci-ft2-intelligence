#!/usr/bin/env python3
import sys
import shutil
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-gb", type=float, default=10)
    parser.add_argument("--path", type=str, default="/")
    args = parser.parse_args()
    
    total, used, free = shutil.disk_usage(args.path)
    free_gb = free / (1024**3)
    
    print(f"📊 Disk Space: {free_gb:.2f} GB free (min: {args.min_gb} GB)")
    
    if free_gb < args.min_gb:
        print("❌ INSUFFICIENT DISK SPACE")
        sys.exit(1)
    
    print("✅ Disk space OK")
    sys.exit(0)

if __name__ == "__main__":
    main()
