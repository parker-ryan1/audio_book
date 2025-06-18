import os
import json
import PyPDF2
import pyttsx3
import pygame
import customtkinter as ctk
from PIL import Image
from datetime import datetime
import threading
import time
import re
import tempfile
import wave

class AudiobookPlayer:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("PDF Audiobook Player")
        self.app.geometry("1200x700")
        ctk.set_appearance_mode("dark")
        
        # Initialize audio engine
        self.engine = pyttsx3.init()
        self.current_book = None
        self.is_playing = False
        self.current_position = 0
        self.playback_speed = 1.0
        self.library = self.load_library()
        self.chapters = []
        self.current_chapter_index = 0
        
        # Configure TTS engine
        self.engine.setProperty('rate', 175)
        self.engine.setProperty('volume', 1.0)
        
        # Get available voices
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)  # Set first available voice
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100)
        pygame.mixer.music.set_volume(1.0)
        
        self.setup_gui()
    
    def setup_gui(self):
        # Create main container
        self.main_container = ctk.CTkFrame(self.app)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create left sidebar
        self.sidebar = ctk.CTkFrame(self.main_container, width=200)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)
        
        # Create right content area
        self.content_area = ctk.CTkFrame(self.main_container)
        self.content_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Sidebar components
        self.add_book_btn = ctk.CTkButton(
            self.sidebar, 
            text="Add Book",
            command=self.add_book
        )
        self.add_book_btn.pack(pady=10, padx=10)
        
        self.library_label = ctk.CTkLabel(self.sidebar, text="Library")
        self.library_label.pack(pady=(20,10))
        
        self.library_list = ctk.CTkScrollableFrame(self.sidebar, width=180, height=400)
        self.library_list.pack(fill="both", expand=True)
        
        # Main content area
        # Top section - Book title and chapter selector
        self.top_section = ctk.CTkFrame(self.content_area)
        self.top_section.pack(fill="x", pady=10)
        
        self.book_title = ctk.CTkLabel(
            self.top_section,
            text="No book selected",
            font=("Arial", 20)
        )
        self.book_title.pack(side="left", pady=10, padx=20)
        
        # Chapter selection
        self.chapter_frame = ctk.CTkFrame(self.content_area)
        self.chapter_frame.pack(fill="x", pady=10)
        
        self.chapter_label = ctk.CTkLabel(self.chapter_frame, text="Chapter:")
        self.chapter_label.pack(side="left", padx=10)
        
        self.chapter_menu = ctk.CTkOptionMenu(
            self.chapter_frame,
            values=["No chapters available"],
            command=self.select_chapter
        )
        self.chapter_menu.pack(side="left", padx=10)
        
        # Progress section
        self.progress_frame = ctk.CTkFrame(self.content_area)
        self.progress_frame.pack(fill="x", pady=10)
        
        self.current_time = ctk.CTkLabel(self.progress_frame, text="0:00")
        self.current_time.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.progress_bar.set(0)
        
        self.total_time = ctk.CTkLabel(self.progress_frame, text="0:00")
        self.total_time.pack(side="right", padx=10)
        
        # Control buttons
        self.controls_frame = ctk.CTkFrame(self.content_area)
        self.controls_frame.pack(pady=20)
        
        self.prev_chapter_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏮",
            width=40,
            command=self.previous_chapter
        )
        self.prev_chapter_btn.pack(side="left", padx=5)
        
        self.play_btn = ctk.CTkButton(
            self.controls_frame,
            text="▶",
            width=40,
            command=self.toggle_play
        )
        self.play_btn.pack(side="left", padx=5)
        
        self.next_chapter_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏭",
            width=40,
            command=self.next_chapter
        )
        self.next_chapter_btn.pack(side="left", padx=5)
        
        # Speed control
        self.speed_frame = ctk.CTkFrame(self.content_area)
        self.speed_frame.pack(pady=10)
        
        self.speed_label = ctk.CTkLabel(self.speed_frame, text="Speed: 1.0x")
        self.speed_label.pack(side="left", padx=10)
        
        self.speed_slider = ctk.CTkSlider(
            self.speed_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=6,
            command=self.change_speed
        )
        self.speed_slider.pack(side="left", padx=10)
        self.speed_slider.set(1.0)
        
        self.update_library_list()
    
    def detect_chapters(self, text):
        # Common chapter patterns
        patterns = [
            r'Chapter \d+',
            r'CHAPTER \d+',
            r'Chapter \d+:.*?(?=Chapter \d+|$)',
            r'CHAPTER \d+:.*?(?=CHAPTER \d+|$)',
        ]
        
        chapters = []
        current_pos = 0
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i+1].start() if i < len(matches)-1 else len(text)
                    chapter_text = text[start:end].strip()
                    chapters.append({
                        'title': match.group(),
                        'start': start,
                        'end': end,
                        'text': chapter_text
                    })
                break  # Use first pattern that finds chapters
        
        if not chapters:
            # If no chapters found, create artificial chapters
            chunk_size = len(text) // 10  # Split into 10 parts
            for i in range(10):
                start = i * chunk_size
                end = start + chunk_size if i < 9 else len(text)
                chapters.append({
                    'title': f'Section {i+1}',
                    'start': start,
                    'end': end,
                    'text': text[start:end].strip()
                })
        
        return chapters
    
    def convert_pdf_to_audio(self, pdf_path, book_id):
        try:
            # Create audio directory if it doesn't exist
            audio_dir = os.path.join(os.path.dirname(__file__), "audio_books")
            os.makedirs(audio_dir, exist_ok=True)
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(pdf_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + " "
            
            # Detect chapters
            chapters = self.detect_chapters(text)
            self.library[book_id]['chapters'] = chapters
            
            # Create audio files for each chapter
            chapter_paths = []
            for i, chapter in enumerate(chapters):
                # First save as WAV
                temp_wav = os.path.join(tempfile.gettempdir(), f"temp_book_{book_id}_chapter_{i}.wav")
                self.engine.save_to_file(chapter['text'], temp_wav)
                self.engine.runAndWait()
                
                # Convert WAV to proper format for pygame
                chapter_audio_path = os.path.join(audio_dir, f"book_{book_id}_chapter_{i}.wav")
                
                # Copy the WAV file to final location
                with wave.open(temp_wav, 'rb') as src:
                    with wave.open(chapter_audio_path, 'wb') as dst:
                        # Copy WAV parameters
                        dst.setnchannels(src.getnchannels())
                        dst.setsampwidth(src.getsampwidth())
                        dst.setframerate(src.getframerate())
                        # Copy audio data
                        dst.writeframes(src.readframes(src.getnframes()))
                
                chapter_paths.append(chapter_audio_path)
                
                # Clean up temp file
                try:
                    os.remove(temp_wav)
                except:
                    pass
            
            # Update book info
            self.library[book_id]["chapter_paths"] = chapter_paths
            self.library[book_id]["current_chapter"] = 0
            self.save_library()
            
            # Update UI if this is the current book
            if self.current_book and self.current_book["id"] == book_id:
                self.app.after(0, self.update_chapter_menu)
            
        except Exception as e:
            print(f"Error converting PDF to audio: {str(e)}")
    
    def select_chapter(self, chapter_title):
        if not self.current_book or 'chapters' not in self.current_book:
            return
        
        try:
            # Find chapter index
            chapters = self.current_book['chapters']
            for i, chapter in enumerate(chapters):
                if chapter['title'] == chapter_title:
                    self.current_chapter_index = i
                    self.current_position = 0
                    
                    # Load and prepare chapter audio
                    if self.is_playing:
                        pygame.mixer.music.stop()
                        self.is_playing = False
                        self.play_btn.configure(text="▶")
                    
                    chapter_path = self.current_book["chapter_paths"][i]
                    if os.path.exists(chapter_path):
                        pygame.mixer.music.load(chapter_path)
                        pygame.mixer.music.play(start=0)
                        pygame.mixer.music.pause()
                        self.update_progress_display()
                    else:
                        print(f"Audio file not found: {chapter_path}")
                    break
        except Exception as e:
            print(f"Error selecting chapter: {str(e)}")
    
    def update_chapter_menu(self):
        if self.current_book and 'chapters' in self.current_book:
            chapter_titles = [chapter['title'] for chapter in self.current_book['chapters']]
            self.chapter_menu.configure(values=chapter_titles)
            self.chapter_menu.set(chapter_titles[self.current_chapter_index])
        else:
            self.chapter_menu.configure(values=["No chapters available"])
            self.chapter_menu.set("No chapters available")
    
    def select_book(self, book_id):
        try:
            # Stop current playback
            if self.is_playing:
                self.toggle_play()
            
            self.current_book = self.library[book_id]
            self.book_title.configure(text=self.current_book["title"])
            
            # Reset playback state
            self.current_chapter_index = self.current_book.get("current_chapter", 0)
            self.current_position = 0
            self.is_playing = False
            self.play_btn.configure(text="▶")
            
            # Update chapter menu
            self.update_chapter_menu()
            
            # Load first chapter
            if "chapter_paths" in self.current_book:
                pygame.mixer.music.load(self.current_book["chapter_paths"][self.current_chapter_index])
                pygame.mixer.music.play(start=0)
                pygame.mixer.music.pause()
            
            self.update_progress_display()
            
        except Exception as e:
            print(f"Error selecting book: {str(e)}")
    
    def toggle_play(self):
        if not self.current_book or "chapter_paths" not in self.current_book:
            return
        
        try:
            chapter_path = self.current_book["chapter_paths"][self.current_chapter_index]
            if not os.path.exists(chapter_path):
                print(f"Audio file not found: {chapter_path}")
                return
            
            if self.is_playing:
                pygame.mixer.music.pause()
                self.play_btn.configure(text="▶")
            else:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.load(chapter_path)
                    pygame.mixer.music.play(start=self.current_position)
                else:
                    pygame.mixer.music.unpause()
                
                self.play_btn.configure(text="⏸")
            
            self.is_playing = not self.is_playing
            
        except Exception as e:
            print(f"Error toggling playback: {str(e)}")
    
    def update_progress_display(self):
        if self.current_book and "chapter_paths" in self.current_book:
            try:
                current_chapter = self.current_book["chapters"][self.current_chapter_index]
                total_text = len(current_chapter["text"])
                progress = self.current_position / total_text if total_text > 0 else 0
                self.progress_bar.set(progress)
                
                # Update time display (approximate based on reading speed)
                words_per_minute = 175  # Based on TTS rate
                total_minutes = len(current_chapter["text"].split()) / words_per_minute
                current_minutes = total_minutes * progress
                
                self.current_time.configure(text=self.format_time(current_minutes * 60))
                self.total_time.configure(text=self.format_time(total_minutes * 60))
                
            except Exception as e:
                print(f"Error updating progress display: {str(e)}")
    
    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def previous_chapter(self):
        if self.current_book and "chapters" in self.current_book:
            self.current_chapter_index = max(0, self.current_chapter_index - 1)
            self.current_position = 0
            self.update_chapter_menu()
            self.select_chapter(self.current_book["chapters"][self.current_chapter_index]["title"])
    
    def next_chapter(self):
        if self.current_book and "chapters" in self.current_book:
            self.current_chapter_index = min(
                len(self.current_book["chapters"]) - 1,
                self.current_chapter_index + 1
            )
            self.current_position = 0
            self.update_chapter_menu()
            self.select_chapter(self.current_book["chapters"][self.current_chapter_index]["title"])
    
    def change_speed(self, value):
        self.playback_speed = value
        self.speed_label.configure(text=f"Speed: {value:.1f}x")
        if self.is_playing:
            self.engine.setProperty('rate', int(175 * value))
    
    def add_book(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            book_name = os.path.basename(file_path)
            book_id = str(len(self.library) + 1)
            
            book_info = {
                "id": book_id,
                "title": book_name,
                "path": file_path,
                "current_chapter": 0,
                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.library[book_id] = book_info
            self.save_library()
            self.update_library_list()
            
            # Convert PDF to audio in background
            threading.Thread(target=self.convert_pdf_to_audio, args=(file_path, book_id)).start()
    
    def load_library(self):
        try:
            with open("library.json", "r") as f:
                return json.load(f)
        except:
            return {}
    
    def save_library(self):
        with open("library.json", "w") as f:
            json.dump(self.library, f)
    
    def update_library_list(self):
        for widget in self.library_list.winfo_children():
            widget.destroy()
        
        for book_id, book_info in self.library.items():
            book_btn = ctk.CTkButton(
                self.library_list,
                text=book_info["title"],
                command=lambda id=book_id: self.select_book(id)
            )
            book_btn.pack(pady=5, fill="x")
    
    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    player = AudiobookPlayer()
    player.run() 