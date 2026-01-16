# RAR Dictionary Cracker

A comprehensive tool for generating custom wordlists and testing RAR archive passwords using dictionary attacks. This project consists of two main components: an advanced wordlist generator and a high-performance RAR password tester.

## Features

### Wordlist Generator (`my_wordlist_generator.py`)
- **Keyword-based generation**: Create wordlists from custom keyword files
- **Multiple generation modes**: Permutations, combinations, or both
- **Pattern insertion**: Automatically insert separators and special characters between keywords
- **Case transformations**: Support for lowercase, uppercase, title case, capitalize, and swapcase
- **Leetspeak transformations**: Basic, extended, and aggressive leet speak with configurable levels
- **Advanced modifications**:
  - Word reversal
  - String prepending/appending
  - Numeric suffix addition with customizable ranges and padding
- **Filtering options**: Length constraints, duplicate removal, empty string filtering
- **High performance**: Multiprocessing support for fast generation of large wordlists

### RAR Password Tester (`direct_rar_tester.py`)
- **Direct RAR testing**: Tests passwords against actual RAR files using the `unrar` command
- **RAR5 compatibility**: Optimized for RAR5 archives with robust error handling
- **Multiple testing modes**:
  - Single password testing
  - Wordlist-based dictionary attacks
- **Parallel processing**: Utilizes multiple CPU cores for significantly faster testing
- **Interactive and CLI modes**: User-friendly interface with command-line options
- **Progress tracking**: Real-time progress updates during wordlist testing
- **Thread-safe operations**: Proper synchronization for concurrent password testing

## Requirements

- **Python 3.6+**
- **unrar** command-line tool (for password testing)
  - Windows: Install from [RARLab](https://www.rarlab.com/rar_add.htm)
  - Linux: `sudo apt-get install unrar` or equivalent
  - macOS: `brew install unrar` or install from RARLab

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/walid-moussa55/rar-dictionary-cracker.git
   cd rar-dictionary-cracker
   ```

2. Ensure Python 3.6+ is installed:
   ```bash
   python --version
   ```

3. Install required Python packages (if any additional dependencies are added):
   ```bash
   pip install -r requirements.txt
   ```

4. Verify `unrar` is installed:
   ```bash
   unrar --version
   ```

## Usage

### Wordlist Generation

Create a keywords file (`keywords.txt`) with one keyword per line:

```
password
admin
user
123
```

#### Basic Usage
```bash
python my_wordlist_generator.py
```

#### Advanced Usage
```bash
# Generate wordlist with leetspeak and case variations
python my_wordlist_generator.py --leet --leet-level 2 --case-mode both

# Add numeric suffixes and filter by length
python my_wordlist_generator.py --add-num --num-start 0 --num-end 999 --min-length 6 --max-length 12

# Use combinations instead of permutations
python my_wordlist_generator.py --mode combination --min-order 2 --max-order 3

# Custom patterns and multiprocessing
python my_wordlist_generator.py -p "!@#,$%^" --processes 4
```

#### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-k, --keywords` | Keywords file | `keywords.txt` |
| `-o, --output` | Output wordlist file | `my_wordlist.txt` |
| `-p, --patterns` | Custom patterns (comma-separated) | Default patterns |
| `--min-order` | Minimum combination order | 1 |
| `--max-order` | Maximum combination order | Number of keywords |
| `--mode` | Generation mode (permutation/combination/both) | permutation |
| `--case-mode` | Case transformation | none |
| `--leet` | Enable leetspeak | False |
| `--leet-level` | Leetspeak level (1-3) | 1 |
| `--prepend` | String to prepend | None |
| `--append` | String to append | None |
| `--add-num` | Add numeric suffixes | False |
| `--num-start` | Numeric suffix start | 0 |
| `--num-end` | Numeric suffix end | 9999 |
| `--num-pad` | Zero-pad width | None |
| `--reverse` | Include reversed versions | False |
| `--min-length` | Minimum entry length | None |
| `--max-length` | Maximum entry length | None |
| `--dedupe` | Remove duplicates | False |
| `--skip-empty` | Skip empty entries | False |
| `--processes` | Number of CPU processes | All available |

### RAR Password Testing

#### Interactive Mode
```bash
python direct_rar_tester.py
```

#### Command Line Mode

Test a single password:
```bash
python direct_rar_tester.py -f archive.rar -p mypassword
```

Test from wordlist:
```bash
python direct_rar_tester.py -f archive.rar -w my_wordlist.txt
```

Test with custom thread count:
```bash
python direct_rar_tester.py -f archive.rar -w my_wordlist.txt -t 8
```

#### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --file` | RAR file to test | Required in CLI mode |
| `-w, --wordlist` | Wordlist file | None |
| `-p, --password` | Single password to test | None |
| `-t, --threads` | Number of parallel workers | CPU cores - 1 |
| `-v, --verbose` | Enable verbose output | False |

## Example Workflow

1. **Create keywords file** (`keywords.txt`):
   ```
   admin
   password
   secret
   123
   ```

2. **Generate wordlist**:
   ```bash
   python my_wordlist_generator.py --leet --case-mode both --add-num --num-end 99
   ```

3. **Test against RAR file**:
   ```bash
   python direct_rar_tester.py -f encrypted.rar -w my_wordlist.txt
   ```

## Performance Considerations

- **Wordlist Generation**:
  - Use multiprocessing (`--processes`) for large keyword sets
  - Enable deduplication (`--dedupe`) to reduce file size
  - Apply length filters to focus on likely passwords

- **Password Testing**:
  - Use multiple threads (`-t`) for faster testing
  - Start with smaller wordlists and common patterns
  - Monitor CPU usage and adjust thread count accordingly

## Troubleshooting

### Common Issues

1. **"unrar command not found"**
   - Install unrar from RARLab or your package manager
   - Ensure unrar is in your system PATH

2. **"No keywords loaded"**
   - Check that `keywords.txt` exists and contains valid keywords
   - Ensure proper file encoding (UTF-8)

3. **Memory issues during generation**
   - Reduce `--max-order` or use fewer keywords
   - Enable `--dedupe` to reduce memory usage
   - Process in smaller chunks

4. **Slow testing performance**
   - Increase thread count if CPU cores are available
   - Use a smaller, more targeted wordlist
   - Check RAR file integrity

## Security Notice

This tool is intended for educational and legitimate purposes only, such as:
- Testing password strength
- Recovering forgotten passwords for your own files
- Security research

**Do not use this tool to:**
- Crack passwords without authorization
- Access protected files without permission
- Violate any laws or terms of service

## Author

**[WAM Development](https://github.com/walid-moussa55)**

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Summary

**RAR Dictionary Cracker** is a powerful, open-source cybersecurity tool designed for password recovery and security testing. This project demonstrates advanced Python programming techniques including multiprocessing, concurrent programming, and system automation.

## Disclaimer

The authors are not responsible for any misuse of this software. Use at your own risk and ensure compliance with applicable laws and regulations.
