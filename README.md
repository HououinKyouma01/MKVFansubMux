# MaikaMux Script

Welcome to the MaikaMux Script! This powerful tool automates the process of muxing MKV files with subtitles, chapters, and fonts using mkvmerge. It's designed to be user-friendly and efficient. Made especially to mke life easier for anime subtitle enthusiasts.
I started this project a long time ago, several fansub groups used it. It was written in C#, but due to the fact that I use different op systems, I decided to rewrite it to a more universal language. 

## ✨ Features

- 🎞️ Automatically mux MKV files with matching subtitles, chapters, and fonts
- 🌈 Colorful and informative console output
- 📊 Real-time progress bar during muxing
- 🔧 Configurable settings via command-line arguments or config file
- 📁 Automatic creation of necessary folders (optional)
- 📝 Detailed logging of warnings and errors (optional)
- 🖥️ Cross-platform support (Windows, macOS, Linux)

## 🚀 Installation

### Prerequisites

- Python 3.6 or higher
- MKVToolNix (mkvmerge)
- Required Python modules: colorama

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/windows/)
2. Install MKVToolNix from [mkvtoolnix.download](https://mkvtoolnix.download/downloads.html#windows)
3. Open Command Prompt and install required Python modules:
   ```
   pip install colorama
   ```
4. Download the `maika-mux.py` script from this repository

### macOS

1. Install Homebrew if not already installed:
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Python and MKVToolNix:
   ```
   brew install python mkvtoolnix
   ```
3. Install required Python modules:
   ```
   pip3 install colorama
   ```
4. Download the `maika-mux.py` script from this repository

### Linux

1. Install Python, pip, and MKVToolNix:
   ```
   sudo apt-get update
   sudo apt-get install python3 python3-pip mkvtoolnix
   ```
2. Install required Python modules:
   ```
   pip3 install colorama
   ```
3. Download the `maika-mux.py` script from this repository

## 🎮 Usage

### Basic Usage

Run the script in the directory containing your MKV files:

```
python maika-mux.py
```

### Specifying Paths

You can specify one or more paths to MKV files or directories:

```
python maika-mux.py path/to/file.mkv path/to/directory
```

### Command-line Options

- `--overwrite`: Overwrite original files (default: True)
- `--no-overwrite`: Do not overwrite original files
- `--create-folders`: Create necessary folders (default: True)
- `--no-create-folders`: Do not create folders
- `--save-log`: Save mux log (default: True)
- `--no-save-log`: Do not save mux log
- `--config`: Edit configuration file

Example:
```
python maika-mux.py --no-overwrite --no-create-folders --no-save-log path/to/files
```

## 🗂️ Directory Structure

The script expects the following directory structure:

```
working_directory/
├── [Group] Series Name - 01 [HASH].mkv
├── subs/
│   ├── [Group] Series Name - 01.ass
│   └── [Group] Series Name - 01_2[Honorifics].ass
├── chapters/
│   └── [Group] Series Name - 01.xml
└── fonts/
    ├── font1.ttf
    └── font2.otf
```

## ⚙️ Configuration

The script creates a `muxer_config.ini` file to store settings. You can edit this file directly or use the `--config` option:

```
python maika-mux.py --config
```

Settings in the config file:
- `MKVMergePath`: Path to the mkvmerge executable
- `OverwriteOriginal`: Whether to overwrite original files (True/False)
- `CreateFolders`: Whether to create necessary folders if they don't exist (True/False)
- `SaveMuxLog`: Whether to save muxing logs (True/False)

## 📋 Logging

If enabled, warnings and errors are logged to `mux.log.txt` in the same directory as the MKV file. The log format is as follows:

```
[YYYY-MM-DD HH:MM:SS]
WARNINGS FOR:
[filename.mkv]

Warning:
[filename.ass] | warning message
The following line will be skipped:
___________________________________________________
Dialogue: 0,0:00:00.00,0:00:00.00,Default,,0,0,0,,Example text
___________________________________________________

```

## 🎨 Color Coding

The console output uses colors for better readability:
- 🔵 Cyan: Muxing process headers
- 🟢 Green: Progress bar and success messages
- 🟡 Yellow: General information and warnings
- 🔴 Red: Errors and important file names

## 📄 License

This script is released under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgements

This script uses [MKVToolNix](https://mkvtoolnix.download/) for muxing operations. Many thanks to the MKVToolNix team for their fantastic work!

---
