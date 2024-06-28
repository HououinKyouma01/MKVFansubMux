# MKV Muxer Script

## Overview

The MKV Muxer Script is a powerful Python utility designed to automate the process of muxing (multiplexing) MKV files with additional subtitle tracks, chapters, and font attachments. This script is particularly useful for anime fansubbers and video enthusiasts who need to combine various elements into a single MKV container.
Compatible with Windows / Linux / Mac OS

## Features

- Automatically detects and muxes multiple subtitle tracks
- Adds chapter files if available
- Includes font attachments
- Cleans existing subtitles, chapters, and attachments before muxing
- Supports custom track naming for subtitle files
- Calculates and updates CRC32 hash in the filename
- Configurable mkvmerge path and overwrite settings
- Option to automatically create necessary folders (subs, chapters, fonts)

## Requirements

- Python 3.6 or higher
- mkvmerge (part of MKVToolNix)

## Installation

1. Ensure you have Python 3.6+ installed on your system.
2. Install MKVToolNix on your system and make sure `mkvmerge` is accessible from the command line.
3. Download the `merge.py` script to your local machine.

## Usage

### Basic Usage

To use the script with default settings:

```
python merge.py [path_to_mkv_file_or_directory]
```

If no path is provided, the script will process all MKV files in the current directory.

### Command-line Options

- `--overwrite`: Overwrite original files (default: False)
- `--config`: Edit the configuration file

Example:
```
python merge.py /path/to/mkv/files --overwrite
```

### Directory Structure

The script expects (or can create, if configured) the following directory structure:

```
working_directory/
├── [Group] Series Name - 01 [WHATEVER][SOMETHING][HASH].mkv
├── subs/
│   ├── [Group] Series Name - 01.ass
│   ├── [Group] Series Name - 01_2.ass
│   └── [Group] Series Name - 01_3[Something].ass
├── chapters/
│   └── [Group] Series Name - 01.xml
└── fonts/
    ├── font1.ttf
    └── font2.otf
```
[Group] Series Name - 01.ass - default track
[Group] Series Name - 01_N.ass - optional subtitle track
[Group] Series Name - 01_N[Something].ass  - optional subtitle track with custom track name

## Configuration

On first run, the script will create a configuration file `muxer_config.ini` in the same directory as the script. You can edit this file directly or use the `--config` option to set:

- Path to mkvmerge
- Whether to overwrite original files by default
- Whether to create necessary folders (subs, chapters, fonts) if they don't exist

### Folder Creation Option

The script includes an option to automatically create the necessary folders (subs, chapters, fonts) if they don't exist. This option is set to `True` by default. You can change this setting in the configuration file or through the `--config` command-line option.

To change this setting:

1. Run the script with the `--config` option:
   ```
   python merge.py --config
   ```
2. When prompted, enter your preference for creating folders (True/False).

Alternatively, you can directly edit the `muxer_config.ini` file and change the `CreateFolders` value:

```ini
[DEFAULT]
MKVMergePath = /path/to/mkvmerge
OverwriteOriginal = True
CreateFolders = True
```

## Functions

### `calculate_crc32(file_path)`

Calculates the CRC32 hash of a given file.

### `load_config()`

Loads or creates the configuration file.

### `extract_file_info(filename)`

Extracts group name, series name, episode number, and hash from the filename.

### `find_files(directory, base_name, ext)`

Finds files matching the given base name and extension in the specified directory.

### `get_track_name(group_name, file_name, index)`

Generates a track name for subtitle files, supporting custom naming for additional tracks.

### `create_folders(mkv_dir)`

Creates the necessary folders (subs, chapters, fonts) if they don't exist.

### `mux_files(mkv_file, mkvmerge_path, overwrite, create_folders_option)`

The main function that performs the muxing operation. It:
1. Creates necessary folders if the option is enabled
2. Extracts file information
3. Finds associated subtitle, chapter, and font files
4. Constructs the mkvmerge command
5. Executes the muxing process
6. Handles file renaming and cleanup

## Customization

### Subtitle Track Naming

The script supports custom naming for additional subtitle tracks. If a subtitle file is named with a pattern like `_2[Honorifics]`, the resulting track name will be "Group Name - Honorifics" instead of "Group Name (Track 2)".

### Font Attachments

All font files in the `fonts/` directory will be attached to the MKV file automatically.

## Troubleshooting

If you encounter any issues:

1. Ensure mkvmerge is correctly installed and its path is set in the configuration.
2. Check that your directory structure matches the expected format, or enable the folder creation option.
3. Verify that you have the necessary permissions to read/write files in the working directory.
4. If the script fails, it will print an error message. Check the console output for details.

## License

This script is released under the MIT License. See the LICENSE file for details.

I DO NOT TAKE RESPONSIBILITY FOR PROGRAM MALFUNCTION, DATA LOSS OR ANYTHING ELSE.
