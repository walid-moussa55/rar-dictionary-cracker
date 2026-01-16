import itertools
import multiprocessing as mp
import sys
import argparse
import random
from functools import partial

# Default patterns with digits included
DEFAULT_PATTERNS = ['', ' ', '<', '!', '.', '_', '+', '(', '"', '|', '¨', '/', "'", '>', '@', ')', '#', '~', '%', '`', '-', ';', ',', '&', '=', '*', '\\', '$', 'é', 'à', 'è', ':', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

# Leetspeak mappings
LEET_MAP = {
    'a': ['4', '@', 'A'],
    'b': ['8', 'B'],
    'e': ['3', 'E'],
    'g': ['6', '9', 'G'],
    'i': ['1', '!', 'I'],
    'l': ['1', 'L'],
    'o': ['0', 'O'],
    's': ['5', '$', 'S'],
    't': ['7', '+', 'T'],
    'z': ['2', 'S'],
}

# Extended leetspeak mappings
LEET_MAP_EXTENDED = {
    'a': ['4', '@', 'A', 'a'],
    'b': ['8', 'B', 'b'],
    'c': ['(', '<', 'C', 'c'],
    'd': [')', 'D', 'd'],
    'e': ['3', 'E', 'e'],
    'f': ['=', 'F', 'f'],
    'g': ['6', '9', 'G', 'g'],
    'h': ['#', 'H', 'h'],
    'i': ['1', '!', 'I', 'i'],
    'j': [']', 'J', 'j'],
    'k': ['<', 'K', 'k'],
    'l': ['1', '|', 'L', 'l'],
    'm': ['M', 'm', '^^'],
    'n': ['N', 'n'],
    'o': ['0', 'O', 'o'],
    'p': ['P', 'p', '9'],
    'q': ['Q', 'q', '9'],
    'r': ['R', 'r'],
    's': ['5', '$', 'S', 's'],
    't': ['7', '+', 'T', 't'],
    'u': ['U', 'u', 'v'],
    'v': ['U', 'v'],
    'w': ['W', 'w', 'vv'],
    'x': ['X', 'x', '><'],
    'y': ['Y', 'y'],
    'z': ['2', 'S', 'z'],
}

def load_keywords(keywords_file):
    """Load keywords from a file, one per line."""
    with open(keywords_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def apply_case_mode(word, case_mode):
    """Apply case transformation to a word."""
    if case_mode == 'lower':
        return word.lower()
    elif case_mode == 'upper':
        return word.upper()
    elif case_mode == 'title':
        return word.title()
    elif case_mode == 'capitalize':
        return word.capitalize()
    elif case_mode == 'swap':
        return word.swapcase()
    else:  # 'none'
        return word

def apply_leet(word, level=1):
    """Apply leetspeak transformation to a word."""
    if level == 0:
        return word
    
    result = []
    leet_map = LEET_MAP_EXTENDED if level >= 2 else LEET_MAP
    
    for char in word:
        lower_char = char.lower()
        if lower_char in leet_map and random.random() > 0.5:
            replacements = leet_map[lower_char]
            result.append(random.choice(replacements))
        else:
            result.append(char)
    
    return ''.join(result)

def filter_by_length(results, min_length, max_length):
    """Filter results by length constraints."""
    if min_length is None and max_length is None:
        return results
    
    filtered = []
    for item in results:
        if min_length is not None and len(item) < min_length:
            continue
        if max_length is not None and len(item) > max_length:
            continue
        filtered.append(item)
    return filtered

def worker(order_chunk, keywords, patterns, output_file, args):
    """Worker function for multiprocessing - writes results directly to file."""
    local_results = []
    
    for order in order_chunk:
        if args.mode in ('permutation', 'both'):
            for permutation in itertools.permutations(keywords, order):
                # Original behavior with patterns
                num_pattern = max(len(permutation) - 1, 1)
                for pattern_comb in itertools.combinations(patterns, min(num_pattern, len(patterns))):
                    combined_list = [item for pair in zip(permutation, pattern_comb + ('',)) for item in pair]
                    local_results.append(''.join(combined_list))
        
        if args.mode in ('combination', 'both') and order > 1:
            for combination in itertools.combinations(keywords, order):
                num_pattern = max(len(combination) - 1, 1)
                for pattern_comb in itertools.combinations(patterns, min(num_pattern, len(patterns))):
                    combined_list = [item for pair in zip(combination, pattern_comb + ('',)) for item in pair]
                    local_results.append(''.join(combined_list))
    
    # Apply transformations
    if args.case_mode != 'none':
        local_results = [apply_case_mode(item, args.case_mode) for item in local_results]
    
    if args.leet:
        leeted_results = []
        for item in local_results:
            leeted_results.append(item)
            if args.leet_level >= 1:
                leeted_results.append(apply_leet(item, args.leet_level))
        local_results = leeted_results
    
    if args.reverse:
        reversed_results = []
        for item in local_results:
            reversed_results.append(item)
            reversed_results.append(item[::-1])
        local_results = reversed_results
    
    if args.prepend:
        local_results = [args.prepend + item for item in local_results]
    
    if args.append:
        local_results = [item + args.append for item in local_results]
    
    # Add number suffix if requested
    if args.add_num:
        num_results = []
        num_start = args.num_start if args.num_start is not None else 0
        num_end = args.num_end if args.num_end is not None else 9999
        num_pad = args.num_pad if args.num_pad is not None else 0
        
        for item in local_results:
            for num in range(num_start, num_end + 1):
                num_str = str(num).zfill(num_pad) if num_pad > 0 else str(num)
                num_results.append(item + num_str)
        local_results = num_results
    
    # Filter by length
    local_results = filter_by_length(local_results, args.min_length, args.max_length)
    
    # Remove empty strings if requested
    if args.skip_empty:
        local_results = [item for item in local_results if item]
    
    # Remove duplicates
    if args.dedupe:
        seen = set()
        deduped = []
        for item in local_results:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        local_results = deduped
    
    # Write chunk to file (append mode)
    with open(output_file, 'a', encoding='utf-8') as f:
        for item in local_results:
            f.write(item + '\n')
    
    return len(local_results)

def main():
    parser = argparse.ArgumentParser(description='Advanced wordlist generator with multiprocessing')
    
    # Core options
    parser.add_argument('-k', '--keywords', default='keywords.txt', 
                        help='File containing keywords (one per line)')
    parser.add_argument('-o', '--output', default='my_wordlist.txt',
                        help='Output wordlist file name')
    parser.add_argument('-p', '--patterns', default='',
                        help='Custom patterns separated by comma (overrides default patterns)')
    
    # Order options
    parser.add_argument('--min-order', type=int, default=1,
                        help='Minimum combination order (default: 1)')
    parser.add_argument('--max-order', type=int, default=None,
                        help='Maximum combination order (default: len(keywords))')
    
    # Mode options
    parser.add_argument('--mode', choices=['permutation', 'combination', 'both'], 
                        default='permutation',
                        help='Generation mode: permutation, combination, or both (default: permutation)')
    
    # Case transformation options
    parser.add_argument('--case-mode', choices=['none', 'lower', 'upper', 'title', 'capitalize', 'swap'], 
                        default='none',
                        help='Case transformation mode (default: none)')
    
    # Leetspeak options
    parser.add_argument('--leet', action='store_true',
                        help='Apply leetspeak transformation')
    parser.add_argument('--leet-level', type=int, default=1, choices=[1, 2, 3],
                        help='Leetspeak level: 1=basic, 2=extended, 3=aggressive (default: 1)')
    
    # Append/Prepend options
    parser.add_argument('--prepend', default='',
                        help='String to prepend to each entry')
    parser.add_argument('--append', default='',
                        help='String to append to each entry')
    
    # Number options
    parser.add_argument('--add-num', action='store_true',
                        help='Add numeric suffix to each entry')
    parser.add_argument('--num-start', type=int, default=None,
                        help='Starting number for numeric suffix (default: 0)')
    parser.add_argument('--num-end', type=int, default=None,
                        help='Ending number for numeric suffix (default: 9999)')
    parser.add_argument('--num-pad', type=int, default=None,
                        help='Zero-pad numbers to this width (e.g., 3 for 001)')
    
    # Reverse option
    parser.add_argument('--reverse', action='store_true',
                        help='Include reversed versions of each entry')
    
    # Length filtering
    parser.add_argument('--min-length', type=int, default=None,
                        help='Minimum entry length')
    parser.add_argument('--max-length', type=int, default=None,
                        help='Maximum entry length')
    
    # Output options
    parser.add_argument('--dedupe', action='store_true',
                        help='Remove duplicate entries')
    parser.add_argument('--skip-empty', action='store_true',
                        help='Skip empty entries')
    
    # Performance options
    parser.add_argument('--processes', type=int, default=None,
                        help='Number of processes to use (default: all CPU cores)')
    
    args = parser.parse_args()
    
    # Load keywords from file
    keywords = load_keywords(args.keywords)
    print(f"Loaded {len(keywords)} keywords from {args.keywords}")
    
    if len(keywords) == 0:
        print("Error: No keywords loaded. Please check the keywords file.")
        sys.exit(1)
    
    # Parse custom patterns or use default
    if args.patterns:
        patterns = args.patterns.split(',')
    else:
        patterns = DEFAULT_PATTERNS
    
    output_file = args.output
    
    # Clear output file
    open(output_file, 'w', encoding='utf-8').close()
    
    # Calculate total orders to process
    max_order = args.max_order if args.max_order else len(keywords)
    orders = list(range(args.min_order, max_order + 1))
    
    # Determine number of processes
    num_processes = args.processes if args.processes else min(mp.cpu_count(), len(orders))
    num_processes = max(1, num_processes)
    
    # Split orders into chunks for each process
    chunk_size = max(1, len(orders) // num_processes)
    chunks = [orders[i:i + chunk_size] for i in range(0, len(orders), chunk_size)]
    
    print(f"Generating wordlist with {num_processes} processes...")
    print(f"Mode: {args.mode}")
    print(f"Orders to process: {orders}")
    print(f"Chunk size: {chunk_size}")
    print(f"Patterns count: {len(patterns)}")
    
    if args.case_mode != 'none':
        print(f"Case mode: {args.case_mode}")
    
    if args.leet:
        print(f"Leetspeak: enabled (level {args.leet_level})")
    
    if args.reverse:
        print("Reverse: enabled")
    
    if args.prepend:
        print(f"Prepend: '{args.prepend}'")
    
    if args.append:
        print(f"Append: '{args.append}'")
    
    if args.add_num:
        print(f"Number suffix: {args.num_start}-{args.num_end} (pad: {args.num_pad})")
    
    if args.min_length or args.max_length:
        print(f"Length filter: {args.min_length}-{args.max_length}")
    
    if args.dedupe:
        print("Deduplication: enabled")
    
    total_count = 0
    
    # Use multiprocessing Pool
    with mp.Pool(processes=num_processes) as pool:
        worker_partial = partial(worker, keywords=keywords, patterns=patterns, output_file=output_file, args=args)
        results = pool.map(worker_partial, chunks)
        total_count = sum(results)
    
    print(f"\nWordlist generated successfully!")
    print(f"Total entries written to {output_file}: {total_count}")

if __name__ == '__main__':
    main()

