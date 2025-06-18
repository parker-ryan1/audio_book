# PDF Audiobook Creator

A Python application that converts PDF documents into audiobooks with features similar to Audible. This application provides a modern, user-friendly interface for managing and listening to your PDF documents as audiobooks.

## Features

- PDF text extraction and processing
- High-quality text-to-speech conversion
- Automatic chapter detection
- Modern GUI with dark mode
- Audiobook library management
- Playback controls:
  - Play/Pause
  - Chapter navigation
  - Variable playback speed (0.5x to 2.0x)
  - Progress tracking
  - Chapter selection

## Screenshots

(Add screenshots of your application here)

## Requirements

- Python 3.8 or higher
- Windows (for text-to-speech support)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pdf-audiobook-creator.git
cd pdf-audiobook-creator
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Click "Add Book" to select a PDF file
3. Wait for the conversion process to complete
4. Select your book from the library
5. Use the chapter dropdown to select a chapter
6. Use playback controls to listen to your audiobook

## How it Works

1. **PDF Processing**: Uses PyPDF2 to extract text from PDF files
2. **Chapter Detection**: Automatically detects chapters using common patterns
3. **Text-to-Speech**: Converts text to speech using pyttsx3
4. **Audio Playback**: Uses pygame for audio playback with controls
5. **GUI**: Built with customtkinter for a modern look

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PyPDF2](https://github.com/py-pdf/PyPDF2) for PDF processing
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) for text-to-speech
- [pygame](https://github.com/pygame/pygame) for audio playback
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI 