import os
import re
import subprocess
import zlib
import configparser
import json
import argparse
import sys
import shutil

CONFIG_FILE = 'muxer_config.ini'

def calculate_crc32(file_path):
    with open(file_path, 'rb') as f:
        return format(zlib.crc32(f.read()) & 0xFFFFFFFF, '08X')

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config['DEFAULT'] = {
            'MKVMergePath': '',
            'OverwriteOriginal': 'True',
            'CreateFolders': 'True'
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
    return config

def extract_file_info(filename):
    pattern = r'\[(.*?)\] (.*?) - (\d+).*\[([A-Z0-9]+)\]\.mkv'
    match = re.match(pattern, filename)
    return match.groups() if match else (None, None, None, None)

def find_files(directory, base_name, ext):
    if not os.path.exists(directory):
        return []
    pattern = re.compile(rf'{re.escape(base_name)}(_\d+)?(\[.*?\])?\.{ext}')
    return sorted([f for f in os.listdir(directory) if pattern.match(f)],
                  key=lambda x: int(re.search(r'_(\d+)', x).group(1)) if '_' in x else 0)

def get_track_name(group_name, file_name, index):
    match = re.search(r'_\d+\[(.*?)\]', file_name)
    return f"{group_name} - {match.group(1)}" if match else f'{group_name} (Track {index+1})'

def create_folders(mkv_dir):
    folders = ['subs', 'chapters', 'fonts']
    for folder in folders:
        folder_path = os.path.join(mkv_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder_path}")

def mux_files(mkv_file, mkvmerge_path, overwrite, create_folders_option):
    mkv_dir, mkv_filename = os.path.split(mkv_file)
    group_name, series_name, episode_number, old_hash = extract_file_info(mkv_filename)
    
    if not all([group_name, series_name, episode_number, old_hash]):
        print(f"Failed to extract info from {mkv_filename}")
        return
    
    if create_folders_option:
        create_folders(mkv_dir)
    
    base_name = f"[{group_name}] {series_name} - {episode_number}"
    subs_files = find_files(os.path.join(mkv_dir, 'subs'), base_name, '(?:ass|srt)')
    chapter_file = os.path.join(mkv_dir, 'chapters', f"{base_name}.xml")
    font_files = [f for f in os.listdir(os.path.join(mkv_dir, 'fonts')) if os.path.isfile(os.path.join(mkv_dir, 'fonts', f))] if os.path.exists(os.path.join(mkv_dir, 'fonts')) else []

    if not subs_files and not os.path.exists(chapter_file) and not font_files:
        print(f"No additional files found for {mkv_filename}")
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

    print("Muxing command:", ' '.join(cmd))

    try:
        subprocess.run(cmd, check=True)
        new_hash = calculate_crc32(temp_filepath)
        new_filename = re.sub(r'\[([A-Z0-9]+)\]\.mkv', f'[{new_hash}].mkv', mkv_filename)
        new_filepath = os.path.join(mkv_dir, new_filename)

        if overwrite:
            os.remove(mkv_file)
            shutil.move(temp_filepath, new_filepath)
            print(f"Original file {mkv_filename} overwritten with new muxed file {new_filename}.")
        else:
            shutil.move(temp_filepath, new_filepath)
            print(f"New muxed file created: {new_filename}")

        print(f"Muxed subtitle tracks:")
        for i, subs_file in enumerate(subs_files):
            track_name = get_track_name(group_name, subs_file, i)
            print(f"  - Track {i+1}: {subs_file} -> {track_name} ({'default' if i == 0 else 'non-default'})")

        if os.path.exists(chapter_file):
            print(f"Muxed chapter file: {os.path.basename(chapter_file)}")

        print(f"Muxed font attachments: {len(font_files)}")

    except subprocess.CalledProcessError as e:
        print(f"Error muxing file {mkv_filename}: {e}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

def find_mkvmerge():
    if sys.platform == "darwin":  # macOS
        common_paths = [
            "/usr/local/bin/mkvmerge",
            "/opt/homebrew/bin/mkvmerge",
            "/usr/bin/mkvmerge"
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    return shutil.which("mkvmerge")

def main():
    parser = argparse.ArgumentParser(description='MKV muxing script using mkvmerge.')
    parser.add_argument('paths', nargs='*', help='Paths to MKV files or directories containing MKV files.')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite original files (default: False)')
    parser.add_argument('--config', action='store_true', help='Edit configuration file')
    args = parser.parse_args()

    config = load_config()
    mkvmerge_path = config['DEFAULT']['MKVMergePath']
    overwrite_original = config.getboolean('DEFAULT', 'OverwriteOriginal')
    create_folders_option = config.getboolean('DEFAULT', 'CreateFolders')

    if args.config:
        mkvmerge_path = input(f"Enter mkvmerge path [{mkvmerge_path}]: ") or mkvmerge_path
        overwrite_original = input(f"Overwrite original files (True/False) [{overwrite_original}]: ") or overwrite_original
        create_folders_option = input(f"Create folders if they don't exist (True/False) [{create_folders_option}]: ") or create_folders_option
        config['DEFAULT']['MKVMergePath'] = mkvmerge_path
        config['DEFAULT']['OverwriteOriginal'] = str(overwrite_original)
        config['DEFAULT']['CreateFolders'] = str(create_folders_option)
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print("Configuration saved.")
        return

    if not mkvmerge_path:
        mkvmerge_path = find_mkvmerge()
        if not mkvmerge_path:
            print("mkvmerge not found. Please install MKVToolNix and set the path manually.")
            mkvmerge_path = input("Enter mkvmerge path: ")
        config['DEFAULT']['MKVMergePath'] = mkvmerge_path
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    paths = args.paths or [os.getcwd()]
    overwrite = args.overwrite or overwrite_original

    for path in paths:
        if os.path.isdir(path):
            for file in os.listdir(path):
                if file.endswith('.mkv'):
                    mux_files(os.path.join(path, file), mkvmerge_path, overwrite, create_folders_option)
        elif os.path.isfile(path) and path.endswith('.mkv'):
            mux_files(path, mkvmerge_path, overwrite, create_folders_option)
        else:
            print(f"Invalid path: {path}")

if __name__ == "__main__":
    main()
