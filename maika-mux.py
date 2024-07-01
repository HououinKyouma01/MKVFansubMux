import os
import re
import subprocess
import zlib
import configparser
import json
import argparse
import sys
import shutil
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init()

CONFIG_FILE = 'muxer_config.ini'

def calculate_crc32(file_path):
    with open(file_path, 'rb') as f:
        return format(zlib.crc32(f.read()) & 0xFFFFFFFF, '08X')

def load_config():
    config = configparser.ConfigParser()
    
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        config['DEFAULT'] = {}

    # Set default values if not present in config
    if 'MKVMergePath' not in config['DEFAULT']:
        mkvmerge_path = find_mkvmerge()
        if mkvmerge_path:
            config['DEFAULT']['MKVMergePath'] = mkvmerge_path
        else:
            print("mkvmerge not found in default locations.")
            mkvmerge_path = input("Please enter the full path to mkvmerge: ")
            config['DEFAULT']['MKVMergePath'] = mkvmerge_path

    if 'OverwriteOriginal' not in config['DEFAULT']:
        config['DEFAULT']['OverwriteOriginal'] = 'True'

    if 'CreateFolders' not in config['DEFAULT']:
        config['DEFAULT']['CreateFolders'] = 'True'

    # Save config if it was modified or created
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
	
    if 'SaveMuxLog' not in config['DEFAULT']:
        config['DEFAULT']['SaveMuxLog'] = 'True'

    return config

def extract_file_info(filename):
    pattern = r'\[(.*?)\] (.*?) - (\d+)(?:.*?(\[[A-Z0-9]+\]))?\.mkv'
    match = re.match(pattern, filename)
    if match:
        group_name, series_name, episode_number, old_hash = match.groups()
        if old_hash:
            old_hash = old_hash[1:-1]  # Remove brackets from the hash
        return group_name, series_name, episode_number, old_hash
    
    # If the first pattern doesn't match, try a more flexible one
    pattern = r'\[(.*?)\] (.*) - (\d+)(?:\s*\[([^\]]+)\])*\.mkv'
    match = re.match(pattern, filename)
    if match:
        group_name, series_name, episode_number, quality = match.groups()
        return group_name, series_name, episode_number, None  # No CRC hash in this format
    
    return None, None, None, None

def find_files(directory, base_name, ext):
    if not os.path.exists(directory):
        return []
    pattern = re.compile(rf'{re.escape(base_name)}(_\d+)?(\[.*?\])?\.{ext}')
    return sorted([f for f in os.listdir(directory) if pattern.match(f)],
                  key=lambda x: int(re.search(r'_(\d+)', x).group(1)) if '_' in x else 0)

def get_track_name(group_name, file_name, index):
    if index == 0:
        return group_name
    
    match = re.search(r'_\d+\[(.*?)\]', file_name)
    if match:
        return f"{group_name} - {match.group(1)}"
    else:
        return f'{group_name} (Track {index+1})'

def create_folders(mkv_dir):
    folders = ['subs', 'chapters', 'fonts']
    for folder in folders:
        folder_path = os.path.join(mkv_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder_path}")

def mux_files(mkv_file, mkvmerge_path, overwrite, create_folders_option, save_log):
    mkv_dir, mkv_filename = os.path.split(mkv_file)
    group_name, series_name, episode_number, old_hash = extract_file_info(mkv_filename)
    
    if not all([group_name, series_name, episode_number]):
        print(f"{Fore.RED}Failed to extract info from {mkv_filename}{Style.RESET_ALL}")
        return
    
    if create_folders_option:
        create_folders(mkv_dir)
    
    base_name = f"[{group_name}] {series_name} - {episode_number}"
    subs_files = find_files(os.path.join(mkv_dir, 'subs'), base_name, '(?:ass|srt)')
    chapter_file = os.path.join(mkv_dir, 'chapters', f"{base_name}.xml")
    font_files = [f for f in os.listdir(os.path.join(mkv_dir, 'fonts')) if os.path.isfile(os.path.join(mkv_dir, 'fonts', f))] if os.path.exists(os.path.join(mkv_dir, 'fonts')) else []

    if not subs_files and not os.path.exists(chapter_file) and not font_files:
        print(f"{Fore.YELLOW}No additional files found for {mkv_filename}{Style.RESET_ALL}")
        return

    temp_filepath = os.path.join(mkv_dir, f"temp_muxed_{mkv_filename}")
    track_info = json.loads(subprocess.check_output([mkvmerge_path, '-J', mkv_file]).decode('utf-8'))

    cmd = [mkvmerge_path, '-o', temp_filepath,
           '--title', f"[{group_name}] {series_name} - {episode_number}",
           '--track-order', ','.join(f"0:{t['id']}" for t in track_info['tracks'] if t['type'] in ['video', 'audio']),
           '--no-subtitles', '--no-chapters', '--no-attachments',
           mkv_file]

    if os.path.exists(chapter_file):
        cmd.extend(['--chapters', chapter_file])

    for i, subs_file in enumerate(subs_files):
        track_name = get_track_name(group_name, subs_file, i)
        cmd.extend(['--language', '0:eng',
                    '--track-name', f'0:{track_name}',
                    '--default-track', '0:yes' if i == 0 else '0:no',
                    '(', os.path.join(mkv_dir, 'subs', subs_file), ')'])

    for font in font_files:
        cmd.extend(['--attachment-mime-type', 'application/x-truetype-font',
                    '--attach-file', os.path.join(mkv_dir, 'fonts', font)])

    log_file = os.path.join(mkv_dir, 'mux.log.txt')
    warnings = []

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        print(f"\n{Fore.CYAN}╔══ Muxing {Fore.WHITE}{mkv_filename}{Fore.CYAN} ══╗{Style.RESET_ALL}")
        for line in process.stdout:
            line = line.strip()
            if line.startswith("Progress:"):
                progress = int(line.split(':')[1].strip().rstrip('%'))
                bar_length = 20
                filled_length = int(bar_length * progress // 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                sys.stdout.write(f"\r{Fore.GREEN}║ Progress: [{bar}] {progress}%{Style.RESET_ALL}")
                sys.stdout.flush()
            elif line.startswith("Warning:"):
                warnings.append(line)
            else:
                def replace_filename(match):
                    full_path = match.group(1) or match.group(2)
                    return f"{Fore.RED}{os.path.basename(full_path)}{Fore.YELLOW}"

                parsed_line = re.sub(r"'?(.+?\.(?:mkv|ass))'?:|'(.+?)'", replace_filename, line)
                print(f"{Fore.YELLOW}║ {parsed_line}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}╚{'═' * (len(mkv_filename) + 10)}╝{Style.RESET_ALL}")
        rc = process.wait()

        if save_log and warnings:
            with open(log_file, 'a') as log:
                log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                log.write("WARNINGS FOR:\n")
                log.write(f"{mkv_filename}\n\n")
                
                for warning in warnings:
                    parsed_warning = re.match(r"Warning: '(.+?)' (.+)", warning)
                    if parsed_warning:
                        file_path, message = parsed_warning.groups()
                        file_name = os.path.basename(file_path)
                        log.write("Warning:\n")
                        log.write(f"{file_name} | {message}\n")
                        
                        if "The following line will be skipped" in message:
                            skipped_line = re.search(r"timestamp: (.+)$", warning)
                            if skipped_line:
                                log.write("The following line will be skipped:\n")
                                log.write("___________________________________________________\n")
                                log.write(f"{skipped_line.group(1)}\n")
                                log.write("___________________________________________________\n")
                    else:
                        log.write(f"{warning}\n")
                    log.write("\n")

        if rc == 0 or rc == 1:  # mkvmerge returns 1 for warnings, but muxing is still successful
            print(f"{Fore.GREEN}✔ Muxing completed successfully.{Style.RESET_ALL}")
            new_hash = calculate_crc32(temp_filepath)
            if old_hash:
                new_filename = re.sub(r'\[([A-Z0-9]+)\]\.mkv', f'[{new_hash}].mkv', mkv_filename)
            else:
                new_filename = f"{os.path.splitext(mkv_filename)[0]}[{new_hash}].mkv"
            new_filepath = os.path.join(mkv_dir, new_filename)

            if overwrite:
                os.remove(mkv_file)
                shutil.move(temp_filepath, new_filepath)
                print(f"{Fore.YELLOW}► Original file overwritten with new muxed file:{Style.RESET_ALL}")
                print(f"  {Fore.WHITE}{new_filename}{Style.RESET_ALL}")
            else:
                shutil.move(temp_filepath, new_filepath)
                print(f"{Fore.YELLOW}► New muxed file created:{Style.RESET_ALL}")
                print(f"  {Fore.WHITE}{new_filename}{Style.RESET_ALL}")

            print(f"\n{Fore.CYAN}Muxed content:{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}► Subtitle tracks:{Style.RESET_ALL}")
            for i, subs_file in enumerate(subs_files):
                track_name = get_track_name(group_name, subs_file, i)
                print(f"  {Fore.WHITE}- Track {i+1}: {subs_file} → {track_name} ({'default' if i == 0 else 'non-default'}){Style.RESET_ALL}")

            if os.path.exists(chapter_file):
                print(f"{Fore.YELLOW}► Chapter file:{Style.RESET_ALL}")
                print(f"  {Fore.WHITE}- {os.path.basename(chapter_file)}{Style.RESET_ALL}")

            print(f"{Fore.YELLOW}► Font attachments:{Style.RESET_ALL}")
            print(f"  {Fore.WHITE}- {len(font_files)} fonts attached{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✘ Error muxing file {mkv_filename}. Check {log_file} for details.{Style.RESET_ALL}")
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

    except Exception as e:
        print(f"{Fore.RED}✘ Error muxing file {mkv_filename}: {str(e)}{Style.RESET_ALL}")
        if save_log:
            with open(log_file, 'a') as log:
                log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                log.write(f"ERROR MUXING: {mkv_filename}\n\n")
                log.write(f"{str(e)}\n\n")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

    if save_log and warnings:
        print(f"{Fore.YELLOW}► Warnings saved to: {log_file}{Style.RESET_ALL}")

def find_mkvmerge():
    if sys.platform == "win32":
        possible_paths = [
            r"C:\Program Files\MKVToolNix\mkvmerge.exe",
            r"C:\Program Files (x86)\MKVToolNix\mkvmerge.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    elif sys.platform == "darwin":  # macOS
        possible_paths = [
            "/usr/local/bin/mkvmerge",
            "/opt/homebrew/bin/mkvmerge",
            "/usr/bin/mkvmerge"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    else:  # Linux and other Unix-like systems
        import shutil
        return shutil.which("mkvmerge")
    
    return None


def main():
    config = load_config()
    mkvmerge_path = config['DEFAULT']['MKVMergePath']
    overwrite_original = config.getboolean('DEFAULT', 'OverwriteOriginal')
    create_folders_option = config.getboolean('DEFAULT', 'CreateFolders')
    save_mux_log = config.getboolean('DEFAULT', 'SaveMuxLog')

    parser = argparse.ArgumentParser(description='MKV muxing script using mkvmerge.')
    parser.add_argument('paths', nargs='*', help='Paths to MKV files or directories containing MKV files.')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite original files')
    parser.add_argument('--no-overwrite', action='store_false', dest='overwrite', help='Do not overwrite original files')
    parser.add_argument('--create-folders', action='store_true', help='Create necessary folders')
    parser.add_argument('--no-create-folders', action='store_false', dest='create_folders', help='Do not create folders')
    parser.add_argument('--save-log', action='store_true', help='Save mux log')
    parser.add_argument('--no-save-log', action='store_false', dest='save_log', help='Do not save mux log')
    parser.add_argument('--config', action='store_true', help='Edit configuration file')
    parser.set_defaults(overwrite=overwrite_original, create_folders=create_folders_option, save_log=save_mux_log)
    args = parser.parse_args()

    if args.config:
        mkvmerge_path = input(f"Enter mkvmerge path [{mkvmerge_path}]: ") or mkvmerge_path
        overwrite_original = input(f"Overwrite original files (True/False) [{overwrite_original}]: ") or overwrite_original
        create_folders_option = input(f"Create folders if they don't exist (True/False) [{create_folders_option}]: ") or create_folders_option
        save_mux_log = input(f"Save mux log (True/False) [{save_mux_log}]: ") or save_mux_log
        config['DEFAULT']['MKVMergePath'] = mkvmerge_path
        config['DEFAULT']['OverwriteOriginal'] = str(overwrite_original)
        config['DEFAULT']['CreateFolders'] = str(create_folders_option)
        config['DEFAULT']['SaveMuxLog'] = str(save_mux_log)
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print("Configuration saved.")
        return

    paths = args.paths or [os.getcwd()]
    overwrite = args.overwrite
    create_folders = args.create_folders
    save_log = args.save_log

    print(f"Overwrite setting: {overwrite}")
    print(f"Create folders setting: {create_folders}")
    print(f"Save log setting: {save_log}")

    for path in paths:
        if os.path.isdir(path):
            for file in os.listdir(path):
                if file.endswith('.mkv'):
                    mux_files(os.path.join(path, file), mkvmerge_path, overwrite, create_folders, save_log)
        elif os.path.isfile(path) and path.endswith('.mkv'):
            mux_files(path, mkvmerge_path, overwrite, create_folders, save_log)
        else:
            print(f"Invalid path: {path}")

if __name__ == "__main__":
    main()