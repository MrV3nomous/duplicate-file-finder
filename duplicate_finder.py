#!/usr/bin/env python3
import os
import hashlib
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.progress import track
from pathlib import Path
import shutil

console = Console()

# ------------------- Utility Functions -------------------

def get_file_hash(file_path, block_size=65536):
    """Compute SHA256 hash of a file."""
    sha = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                sha.update(block)
    except Exception as e:
        console.print(f"[red]Error reading {file_path}: {e}[/red]")
        return None
    return sha.hexdigest()

def scan_folder(folder_path):
    """Scan folder and return a dict of file hash -> list of paths."""
    duplicates = defaultdict(list)
    folder_path = Path(folder_path)
    all_files = [p for p in folder_path.rglob("*") if p.is_file()]

    for file in track(all_files, description="Scanning files..."):
        file_hash = get_file_hash(file)
        if file_hash:
            duplicates[file_hash].append(file)

    # Filter only hashes with multiple files
    return {h: paths for h, paths in duplicates.items() if len(paths) > 1}

def display_duplicates(dupes):
    """Display duplicates in a nice table."""
    if not dupes:
        console.print("[green]No duplicates found![/green]")
        return

    table = Table(title="Duplicate Files Found", show_lines=True)
    table.add_column("Group #", style="cyan", justify="center")
    table.add_column("File Path", style="magenta")
    table.add_column("Size (MB)", style="yellow", justify="right")

    for idx, (hash_val, files) in enumerate(dupes.items(), start=1):
        for i, f in enumerate(files):
            size_mb = f.stat().st_size / (1024*1024)
            table.add_row(str(idx) if i==0 else "", str(f), f"{size_mb:.2f}")
    console.print(table)

def delete_duplicates(dupes):
    """Allow user to delete duplicate files, keeping one."""
    for hash_val, files in dupes.items():
        console.print(f"\n[cyan]Group {hash_val[:8]}...[/cyan]")
        for i, f in enumerate(files):
            console.print(f"[{i}] {f} ({f.stat().st_size/1024:.1f} KB)")
        keep = console.input("Enter index to keep (comma for multiple, leave empty to skip): ")
        keep_idxs = set(map(int, keep.split(","))) if keep else set()
        for i, f in enumerate(files):
            if i not in keep_idxs:
                try:
                    f.unlink()
                    console.print(f"[red]Deleted[/red] {f}")
                except Exception as e:
                    console.print(f"[red]Failed to delete {f}: {e}[/red]")

# ------------------- Main Menu -------------------

def menu():
    while True:
        console.print("\n[bold green]Elite Duplicate File Finder[/bold green]")
        console.print("[1] Scan folder for duplicates")
        console.print("[2] Exit")
        choice = console.input("Choose an option: ")

        if choice == "1":
            folder = console.input("Enter folder path: ").strip()
            if not os.path.exists(folder):
                console.print("[red]Folder does not exist![/red]")
                continue
            dupes = scan_folder(folder)
            display_duplicates(dupes)
            if dupes:
                delete_choice = console.input("Delete duplicates? (y/n): ").lower()
                if delete_choice == "y":
                    delete_duplicates(dupes)
        elif choice == "2":
            console.print("[bold yellow]Exiting...[/bold yellow]")
            break
        else:
            console.print("[red]Invalid choice, try again.[/red]")

# ------------------- Entry Point -------------------

if __name__ == "__main__":
    menu()
