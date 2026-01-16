#!/usr/bin/env python3
"""
Direct Password Tester for RAR5
Tests passwords against the actual RAR file using multiprocessing for speed
"""

import subprocess
import sys
import os
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import threading


# Global lock for thread-safe output
output_lock = threading.Lock()
found_password = None
found_lock = threading.Lock()


def find_rar_files():
    """Find all RAR files in current directory"""
    rar_files = [f for f in os.listdir('.') if f.lower().endswith('.rar')]
    return rar_files


def select_rar_file():
    """Let user select a RAR file from available options"""
    rar_files = find_rar_files()
    
    if not rar_files:
        print("❌ No RAR files found in current directory")
        return None
    
    if len(rar_files) == 1:
        return rar_files[0]
    
    print("\n📦 Available RAR files:")
    for i, rf in enumerate(rar_files, 1):
        print(f"  {i}. {rf}")
    
    while True:
        choice = input(f"\nSelect RAR file (1-{len(rar_files)}): ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(rar_files):
                return rar_files[idx - 1]
        except ValueError:
            pass
        print("Invalid choice, please try again.")


def test_password_worker(args):
    """
    Worker function for multiprocessing - tests a single password
    Returns tuple: (is_correct, password, method)
    """
    password, rar_file = args
    
    # First check with unrar t (test archive) - most reliable
    try:
        cmd = ['unrar', 't', f'-p{password}', rar_file]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout + result.stderr
        
        # Check if test passed - "All OK" means correct password
        if "All OK" in output:
            return (True, password, "unrar t")
        
        # Check if password is definitely wrong
        if "Incorrect password" in output or "Wrong password" in output:
            return (False, password, "wrong")
        
        # If unrar t doesn't give clear result, try unrar lt
        # This handles some RAR5 edge cases
        if result.returncode == 0:
            cmd2 = ['unrar', 'lt', f'-p{password}', rar_file]
            result2 = subprocess.run(
                cmd2,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output2 = result2.stdout + result2.stderr
            
            # For unrar lt, success means returncode=0 AND no wrong password message
            # AND must have some content (file listing)
            if result2.returncode == 0:
                if "Incorrect password" not in output2 and "Wrong password" not in output2:
                    # Check if we actually got some file listing
                    if "README" in output2 or ".txt" in output2 or "files" in output2.lower():
                        return (True, password, "unrar lt")
            
            # Check if wrong password
            if "Incorrect password" in output2 or "Wrong password" in output2:
                return (False, password, "wrong")
    
    except Exception:
        pass
    
    return (False, password, "error")


def test_password_directly(password, rar_file):
    """Test a single password against RAR file (for single password mode)"""
    is_correct, result_password, method = test_password_worker((password, rar_file))
    
    if is_correct:
        with output_lock:
            print(f"\n{'='*60}")
            print(f"✅✅✅ CORRECT PASSWORD FOUND! ✅✅✅")
            print(f"   Password: '{result_password}'")
            print(f"   Method: {method}")
            print(f"   Use: unrar x -p'{result_password}' {rar_file}")
            print(f"{'='*60}\n")
    else:
        with output_lock:
            if method == "wrong":
                print(f"❌ Wrong password: '{password}'")
            else:
                print(f"⚠ Error testing password: '{password}'")
    
    return is_correct


def test_from_wordlist(wordlist_file, rar_file, num_workers=None):
    """Test all passwords from a wordlist using multiprocessing"""
    if not os.path.exists(wordlist_file):
        print(f"❌ Wordlist not found: {wordlist_file}")
        return None
    
    # Read passwords
    with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
        passwords = [line.strip() for line in f if line.strip()]
    
    if not passwords:
        print("❌ No passwords in wordlist")
        return None
    
    # Determine number of workers
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)  # Leave one CPU free
    
    print(f"🔍 Testing passwords from: {wordlist_file}")
    print(f"📦 Against RAR file: {rar_file}")
    print(f"🚀 Using {num_workers} parallel workers")
    print(f"📊 Total passwords: {len(passwords):,}")
    print(f"{'='*60}")
    
    global found_password
    found_password = None
    
    # Prepare arguments for workers
    worker_args = [(pwd, rar_file) for pwd in passwords]
    
    completed = 0
    total = len(passwords)
    
    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all jobs
        futures = {executor.submit(test_password_worker, args): args[0] 
                   for args in worker_args}
        
        # Process results as they complete
        for future in as_completed(futures):
            password = futures[future]
            completed += 1
            
            try:
                is_correct, result_password, method = future.result()
                
                if is_correct:
                    with found_lock:
                        if found_password is None:
                            found_password = result_password
                            # Cancel remaining jobs
                            for f in futures:
                                f.cancel()
                            print(f"\n{'='*60}")
                            print(f"🎉🎉🎉 PASSWORD FOUND! 🎉🎉🎉")
                            print(f"   Password: '{result_password}'")
                            print(f"   Method: {method}")
                            print(f"   Use: unrar x -p'{result_password}' {rar_file}")
                            print(f"{'='*60}\n")
                            break
                else:
                    with output_lock:
                        if completed % 10 == 0 or completed == total:
                            print(f"  Progress: {completed}/{total} ({completed/total*100:.1f}%) - Last checked: '{password}'")
            
            except Exception as e:
                with output_lock:
                    print(f"  Error testing '{password}': {e}")
    
    if found_password:
        return found_password
    else:
        print(f"\n❌ No correct password found after testing {total} passwords")
        return None


def create_arg_parser():
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="🔓 Direct RAR Password Tester (Multiprocessing)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Test a single password:
    %(prog)s -f archive.rar -p mypassword
  
  Test all passwords from wordlist:
    %(prog)s -f archive.rar -w wordlist.txt
  
  Test with specific number of threads:
    %(prog)s -f archive.rar -w wordlist.txt -t 8
  
  Interactive mode (no arguments):
    %(prog)s
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        metavar='FILE',
        help='RAR file to test (required for CLI mode)'
    )
    
    parser.add_argument(
        '-w', '--wordlist',
        metavar='FILE',
        help='Wordlist file containing passwords to test'
    )
    
    parser.add_argument(
        '-p', '--password',
        metavar='PASSWORD',
        help='Single password to test'
    )
    
    parser.add_argument(
        '-t', '--threads',
        type=int,
        metavar='N',
        default=max(1, cpu_count() - 1),
        help=f'Number of parallel workers (default: {max(1, cpu_count() - 1)})'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0'
    )
    
    return parser


def run_cli_mode(args, parser):
    """Run the CLI mode with parsed arguments"""
    rar_file = args.file
    
    # Validate RAR file
    if not rar_file:
        print("❌ Error: RAR file (-f/--file) is required for CLI mode")
        print()
        parser.print_help()
        return
    
    if not os.path.exists(rar_file):
        print(f"❌ Error: RAR file not found: {rar_file}")
        return
    
    print(f"📦 Using RAR file: {rar_file}")
    print(f"🖥️  CPU cores available: {cpu_count()}")
    print(f"🚀 Using {args.threads} parallel workers")
    print("="*60)
    
    # Validate arguments
    password_count = 0
    
    if args.password:
        password_count = 1
        if args.verbose:
            print(f"🔑 Testing single password: '{args.password}'")
        test_password_directly(args.password, rar_file)
    
    if args.wordlist:
        if password_count > 0:
            print("\n⚠️  Both -p/--password and -w/--wordlist specified.")
            print("    Using wordlist only (password ignored)")
        if args.verbose:
            print(f"📖 Loading wordlist: {args.wordlist}")
        test_from_wordlist(args.wordlist, rar_file, num_workers=args.threads)


def run_interactive_mode():
    """Run the interactive mode"""
    print("="*60)
    print("🔓 DIRECT RAR PASSWORD TESTER (Multiprocessing)")
    print("="*60)
    
    # Get RAR file
    rar_file = select_rar_file()
    
    if not rar_file:
        return
    
    print(f"🖥️  CPU cores available: {cpu_count()}")
    
    print("\nOptions:")
    print("  1. Test specific password")
    print("  2. Test from wordlist (single process)")
    print("  3. Test from wordlist (parallel - recommended)")
    print("  c. Choose different RAR file")
    print("  q. Quit")
    
    choice = input("\nEnter choice (1, 2, 3, c, or q): ").strip()
    
    if choice == '1':
        password = input("Enter password to test: ").strip()
        test_password_directly(password, rar_file)
    elif choice == '2':
        wordlist = input("Enter wordlist filename: ").strip()
        if not wordlist:
            wordlist = "my_wordlist.txt"
        test_from_wordlist(wordlist, rar_file, num_workers=1)
    elif choice == '3':
        wordlist = input("Enter wordlist filename: ").strip()
        if not wordlist:
            wordlist = "my_wordlist.txt"
        workers = input(f"Number of workers (default: {max(1, cpu_count()-1)}): ").strip()
        if workers:
            workers = int(workers)
        else:
            workers = max(1, cpu_count() - 1)
        test_from_wordlist(wordlist, rar_file, num_workers=workers)
    elif choice.lower() == 'c':
        run_interactive_mode()  # Restart with new selection
    elif choice.lower() == 'q':
        print("Goodbye!")
    else:
        print("❌ Invalid choice")


def main():
    """Main function with argument parsing"""
    parser = create_arg_parser()
    args = parser.parse_args()
    
    # Check if any arguments were provided
    if len(sys.argv) == 1:
        # No arguments - run in interactive mode
        run_interactive_mode()
    else:
        # CLI mode with arguments
        run_cli_mode(args, parser)


if __name__ == "__main__":
    main()

