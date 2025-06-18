# Audiobook Player

A modern, feature-rich audiobook player built with Python and customtkinter. Converts text files to speech with a beautiful Audible-inspired interface.

## Features

- 🎧 Text-to-Speech playback with Windows SAPI
- 🎨 Beautiful dark theme inspired by Audible
- ⏯️ Play/Pause with progress tracking
- ⏩ Speed control (0.5x - 2.0x)
- ⏪ Forward/Rewind 30 seconds
- 🕒 Sleep timer
- 📚 Library management
- 🔖 Bookmarking system
- 💾 Progress saving
- 📖 Support for text files

## Screenshots

(Add screenshots of your application here)

## Requirements

- Windows 10/11 (for SAPI text-to-speech)
- Python 3.8+
- customtkinter
- pywin32

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/audiobook-player.git
cd audiobook-player
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Click "Add Book" to add text files to your library
3. Select a book from your library to start playing
4. Use the controls to:
   - Play/Pause
   - Adjust speed
   - Skip forward/backward
   - Set sleep timer
   - Add bookmarks

## How it Works

1. **Text-to-Speech**: Converts text to speech using Windows SAPI
2. **GUI**: Built with customtkinter for a modern look
3. **Progress Tracking**: Tracks playback progress
4. **Speed Control**: Allows adjusting playback speed
5. **Sleep Timer**: Adds a sleep timer to the playback
6. **Library Management**: Manages a library of text files
7. **Bookmarking System**: Allows adding bookmarks
8. **Progress Saving**: Saves playback progress

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)

## Acknowledgments

- [PyPDF2](https://github.com/py-pdf/PyPDF2) for PDF processing
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) for text-to-speech
- [pygame](https://github.com/pygame/pygame) for audio playback
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI 