#!/usr/bin/env python3
import os
import sys
import time
import unicodedata

# ANSI Escape Sequences for Colors and Clearing
RESET = "\033[0m"
BRIGHT_MAGENTA = "\033[38;2;255;0;255m"  # Bright magenta for percentage
CYBER_GREEN = "\033[38;2;0;255;128m"    # Cyberpunk green
CYBER_CYAN = "\033[38;2;0;255;255m"     # Cyberpunk cyan
CLEAR_LINE = "\033[K"

def format_mb(bytes_size):
    """Convert bytes to megabytes."""
    return bytes_size / 1_048_576

def format_gb(bytes_size):
    """Convert bytes to gigabytes."""
    return bytes_size / 1_073_741_824

def safe_string(string):
    """Safely clean filenames by replacing problematic characters."""
    return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore').decode('ascii', errors='replace')

def print_progress_line(progress_percentage, transferred_gb, total_gb, speed_mb_s, eta_minutes):
    """Print a clean single-line progress update with bright colors."""
    print(f"\r{CLEAR_LINE}[{BRIGHT_MAGENTA}{progress_percentage:.2f}%{RESET}] "
          f"[{CYBER_CYAN}{transferred_gb:.2f}/{total_gb:.2f} GB{RESET}] "
          f"[{CYBER_GREEN}{speed_mb_s:.2f} MB/s{RESET}] "
          f"[{CYBER_CYAN}{eta_minutes:.0f} min{RESET}]", end="")

def transfer_directory(source_dir, destination_dir):
    """Transfer a directory with resume capability, error handling, and progress display."""
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir, exist_ok=True)

    # Build file list and calculate total size
    files_list = []
    total_size_bytes = 0
    for root, _, filenames in os.walk(source_dir, followlinks=False):
        for filename in filenames:
            try:
                source_path = os.path.join(root, filename)
                if not os.path.islink(source_path):  # Skip symbolic links
                    files_list.append(source_path)
                    total_size_bytes += os.path.getsize(source_path)
            except PermissionError:
                print(f"\n⚠️ Permission Denied: {root}/{filename}")
                continue

    completed_bytes = 0
    total_gb = format_gb(total_size_bytes)
    start_time = time.time()
    resume_notified = False  # To track whether resume notice has been printed

    for file_path in files_list:
        try:
            file_name = os.path.basename(file_path)
            sanitized_file_name = safe_string(file_name)  # Sanitize filename
            dest_path = os.path.join(destination_dir, os.path.relpath(file_path, source_dir))

            # Sanitize the full destination path
            dest_path = os.path.join(os.path.dirname(dest_path), sanitized_file_name)

            # Ensure the destination folder exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Skip already transferred files
            if os.path.exists(dest_path) and os.path.getsize(file_path) == os.path.getsize(dest_path):
                completed_bytes += os.path.getsize(file_path)
                continue

            # Notify on resume (print only once)
            if not resume_notified:
                print(f"\n🔄 Transferring first file not already present: {CYBER_CYAN}{file_name}{RESET}")
                resume_notified = True

            file_size = os.path.getsize(file_path)
            transferred_bytes = 0
            file_start_time = time.time()

            with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
                while chunk := src.read(1024 * 1024):  # 1MB chunks
                    dst.write(chunk)
                    transferred_bytes += len(chunk)
                    completed_bytes += len(chunk)

                    # Update stats
                    elapsed_time = time.time() - start_time
                    progress_percentage = (completed_bytes / total_size_bytes) * 100
                    transferred_gb = format_gb(completed_bytes)
                    speed_mb_s = format_mb(completed_bytes / elapsed_time) if elapsed_time > 0 else 0
                    eta_seconds = ((elapsed_time / progress_percentage) * (100 - progress_percentage)) if progress_percentage > 0 else 0
                    eta_minutes, _ = divmod(int(eta_seconds), 60)

                    # Print single-line progress
                    print_progress_line(progress_percentage, transferred_gb, total_gb, speed_mb_s, eta_minutes)

        except (PermissionError, OSError) as e:
            print(f"\n⚠️ Error transferring '{safe_string(file_path)}': {e}")

    print(f"\n\n🎉 {CYBER_GREEN}Transfer Completed Successfully!{RESET}")

def main():
    if len(sys.argv) != 4:
        print("Usage: transfer <copy|move> <source_path> <destination_path>")
        sys.exit(1)

    source = sys.argv[2]
    destination = sys.argv[3]

    if not os.path.exists(source):
        print(f"❌ Error: Source path '{source}' does not exist.")
        sys.exit(1)

    transfer_directory(source, destination)

if __name__ == "__main__":
    main()
