import os
import json
import customtkinter as ctk
from datetime import datetime
import threading
import win32com.client
import time

class AudiobookPlayer:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Audiobook Player")
        self.app.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        
        # Initialize text-to-speech
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        self.speaker.Rate = 1  # -10 to 10
        self.speaker.Volume = 100  # 0 to 100
        
        # Initialize state
        self.current_book = None
        self.is_playing = False
        self.current_text = ""
        self.current_position = 0
        self.total_length = 0
        self.play_thread = None
        self.playback_speed = 1.0
        
        # Sleep timer
        self.sleep_timer = None
        self.sleep_time_remaining = 0
        
        # Load saved data
        self.library = self.load_library()
        self.bookmarks = self.load_bookmarks()
        
        self.setup_gui()
        
        # Check for last played book
        last_book = self.get_last_played_book()
        if last_book:
            self.show_resume_dialog(last_book)

    def setup_gui(self):
        """Set up the GUI elements."""
        # Create main frame with Audible-like dark theme
        self.app.configure(fg_color="#232F3E")  # Audible's dark blue
        main_frame = ctk.CTkFrame(self.app, fg_color="#232F3E")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title with Audible-like styling
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Audiobook Player", 
            font=("Arial", 28, "bold"),
            text_color="#FF9900"  # Audible's orange
        )
        title_label.pack(pady=10)
        
        # Library section
        self.setup_library_section(main_frame)
        
        # Player section
        self.setup_player_section(main_frame)
        
        # Bottom controls
        self.setup_bottom_controls(main_frame)

    def setup_library_section(self, parent):
        library_frame = ctk.CTkFrame(parent, fg_color="#2F3F4F")
        library_frame.pack(fill="x", padx=10, pady=5)
        
        # Library header
        header = ctk.CTkFrame(library_frame, fg_color="#2F3F4F")
        header.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text="Your Library",
            font=("Arial", 18, "bold"),
            text_color="#FF9900"
        ).pack(side="left", padx=10)
        
        # Add book button
        self.add_book_btn = ctk.CTkButton(
            header,
            text="+ Add Book",
            font=("Arial", 12),
            fg_color="#FF9900",
            text_color="#232F3E",
            hover_color="#FFB84D",
            command=self.add_book
        )
        self.add_book_btn.pack(side="right", padx=10)
        
        # Book list
        self.book_list = ctk.CTkScrollableFrame(
            library_frame,
            fg_color="#2F3F4F",
            height=150
        )
        self.book_list.pack(fill="x", padx=10, pady=5)

    def setup_player_section(self, parent):
        player_frame = ctk.CTkFrame(parent, fg_color="#2F3F4F")
        player_frame.pack(fill="x", padx=10, pady=10)
        
        # Current book info
        info_frame = ctk.CTkFrame(player_frame, fg_color="#2F3F4F")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        self.book_title = ctk.CTkLabel(
            info_frame,
            text="No book selected",
            font=("Arial", 16, "bold"),
            text_color="#FFFFFF"
        )
        self.book_title.pack(pady=5)
        
        # Progress bar and time
        progress_frame = ctk.CTkFrame(player_frame, fg_color="#2F3F4F")
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.current_time = ctk.CTkLabel(
            progress_frame,
            text="0:00",
            text_color="#B4B4B4"
        )
        self.current_time.pack(side="left")
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            progress_color="#FF9900",
            height=8
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        self.progress_bar.set(0)
        
        self.total_time = ctk.CTkLabel(
            progress_frame,
            text="0:00",
            text_color="#B4B4B4"
        )
        self.total_time.pack(side="right")

    def setup_bottom_controls(self, parent):
        controls_frame = ctk.CTkFrame(parent, fg_color="#2F3F4F")
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Main controls
        main_controls = ctk.CTkFrame(controls_frame, fg_color="#2F3F4F")
        main_controls.pack(pady=10)
        
        # Rewind 30s
        self.rewind_btn = ctk.CTkButton(
            main_controls,
            text="⟲ 30",
            width=40,
            fg_color="#3F4F5F",
            hover_color="#4F5F6F",
            command=self.rewind_30
        )
        self.rewind_btn.pack(side="left", padx=5)
        
        # Play/Pause
        self.play_btn = ctk.CTkButton(
            main_controls,
            text="▶",
            width=60,
            fg_color="#FF9900",
            hover_color="#FFB84D",
            command=self.toggle_play
        )
        self.play_btn.pack(side="left", padx=10)
        
        # Forward 30s
        self.forward_btn = ctk.CTkButton(
            main_controls,
            text="⟳ 30",
            width=40,
            fg_color="#3F4F5F",
            hover_color="#4F5F6F",
            command=self.forward_30
        )
        self.forward_btn.pack(side="left", padx=5)
        
        # Bottom row controls
        bottom_row = ctk.CTkFrame(controls_frame, fg_color="#2F3F4F")
        bottom_row.pack(fill="x", pady=5)
        
        # Speed control
        speed_frame = ctk.CTkFrame(bottom_row, fg_color="#2F3F4F")
        speed_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            speed_frame,
            text="Speed",
            text_color="#B4B4B4"
        ).pack(side="left", padx=5)
        
        self.speed_menu = ctk.CTkOptionMenu(
            speed_frame,
            values=["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"],
            command=self.change_speed,
            fg_color="#3F4F5F",
            button_color="#3F4F5F",
            button_hover_color="#4F5F6F"
        )
        self.speed_menu.pack(side="left", padx=5)
        self.speed_menu.set("1.0x")
        
        # Sleep timer
        self.sleep_btn = ctk.CTkButton(
            bottom_row,
            text="🕒 Sleep Timer",
            fg_color="#3F4F5F",
            hover_color="#4F5F6F",
            command=self.set_sleep_timer
        )
        self.sleep_btn.pack(side="right", padx=10)
        
        # Bookmark button
        self.bookmark_btn = ctk.CTkButton(
            bottom_row,
            text="🔖",
            width=30,
            fg_color="#3F4F5F",
            hover_color="#4F5F6F",
            command=self.show_bookmarks
        )
        self.bookmark_btn.pack(side="right", padx=5)

    def play_text(self):
        """Play the text using text-to-speech."""
        try:
            if self.current_text:
                print("Starting text playback")
                # Split text into manageable chunks
                chunk_size = 1000  # characters
                chunks = [self.current_text[i:i+chunk_size] 
                         for i in range(0, len(self.current_text), chunk_size)]
                
                print(f"Total chunks: {len(chunks)}")
                self.total_length = len(chunks)
                start_chunk = int(self.current_position * self.total_length)
                print(f"Starting from chunk: {start_chunk}")
                
                for i in range(start_chunk, len(chunks)):
                    if not self.is_playing:
                        print("Playback stopped")
                        break
                    
                    chunk = chunks[i]
                    print(f"Playing chunk {i} of {len(chunks)}")
                    self.speaker.Speak(chunk)
                    
                    # Update progress
                    self.current_position = i / self.total_length
                    self.update_progress()
                    
                    # Check sleep timer
                    if self.sleep_timer and time.time() >= self.sleep_timer:
                        print("Sleep timer triggered")
                        self.is_playing = False
                        self.sleep_timer = None
                        break
                
                if self.is_playing:
                    print("Playback completed")
                    self.is_playing = False
                    self.play_btn.configure(text="▶")
                
        except Exception as e:
            print(f"Error playing text: {str(e)}")
            import traceback
            traceback.print_exc()
            self.is_playing = False
            self.play_btn.configure(text="▶")

    def toggle_play(self):
        """Toggle audio playback."""
        if not self.current_book:
            print("No book selected")
            return
        
        try:
            if self.is_playing:
                print("Stopping playback")
                self.is_playing = False
                self.speaker.Speak("", 2)  # Stop speaking
                if self.play_thread:
                    print("Waiting for thread to finish")
                    self.play_thread.join()
                self.play_btn.configure(text="▶")
            else:
                print("Starting playback")
                if not self.current_text:
                    print("No text loaded")
                    return
                print(f"Text length: {len(self.current_text)}")
                print(f"Current position: {self.current_position}")
                self.is_playing = True
                self.play_thread = threading.Thread(target=self.play_text)
                self.play_thread.daemon = True
                self.play_thread.start()
                self.play_btn.configure(text="⏸")
            
            # Update last played time
            self.current_book['last_played'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_library()
            
        except Exception as e:
            print(f"Error toggling playback: {str(e)}")
            import traceback
            traceback.print_exc()

    def rewind_30(self):
        """Rewind 30 seconds."""
        if self.current_text:
            # Estimate 30 seconds worth of text
            chunk_size = 1000  # characters
            chunks_per_second = 3  # rough estimate
            chunks_to_move = 30 * chunks_per_second
            
            new_pos = max(0, self.current_position - (chunks_to_move / self.total_length))
            self.current_position = new_pos
            self.update_progress()

    def forward_30(self):
        """Forward 30 seconds."""
        if self.current_text:
            # Estimate 30 seconds worth of text
            chunk_size = 1000  # characters
            chunks_per_second = 3  # rough estimate
            chunks_to_move = 30 * chunks_per_second
            
            new_pos = min(1, self.current_position + (chunks_to_move / self.total_length))
            self.current_position = new_pos
            self.update_progress()

    def change_speed(self, speed):
        """Change playback speed."""
        speed_value = float(speed.replace('x', ''))
        self.playback_speed = speed_value
        self.speaker.Rate = int((speed_value - 1) * 10)  # Convert to SAPI5 rate (-10 to 10)

    def set_sleep_timer(self):
        """Set sleep timer dialog."""
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Sleep Timer")
        dialog.geometry("250x300")
        dialog.configure(fg_color="#232F3E")
        
        ctk.CTkLabel(
            dialog,
            text="Stop playing after:",
            font=("Arial", 14, "bold"),
            text_color="#FF9900"
        ).pack(pady=10)
        
        times = ["Off", "15 minutes", "30 minutes", "45 minutes", "60 minutes"]
        
        for time_str in times:
            btn = ctk.CTkButton(
                dialog,
                text=time_str,
                fg_color="#3F4F5F",
                hover_color="#4F5F6F",
                command=lambda t=time_str: self.start_sleep_timer(t)
            )
            btn.pack(pady=5, padx=20, fill="x")

    def start_sleep_timer(self, time_str):
        """Start the sleep timer."""
        if time_str == "Off":
            self.sleep_timer = None
            return
        
        minutes = int(time_str.split()[0])
        self.sleep_timer = time.time() + (minutes * 60)

    def show_bookmarks(self):
        """Show bookmarks dialog."""
        if not self.current_book:
            return
        
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Bookmarks")
        dialog.geometry("400x500")
        dialog.configure(fg_color="#232F3E")
        
        ctk.CTkLabel(
            dialog,
            text="Bookmarks",
            font=("Arial", 18, "bold"),
            text_color="#FF9900"
        ).pack(pady=10)
        
        # Add bookmark button
        add_btn = ctk.CTkButton(
            dialog,
            text="Add Bookmark",
            fg_color="#FF9900",
            text_color="#232F3E",
            hover_color="#FFB84D",
            command=lambda: self.add_bookmark(dialog)
        )
        add_btn.pack(pady=10)
        
        # Show existing bookmarks
        book_id = self.current_book['id']
        if book_id in self.bookmarks:
            for bookmark in self.bookmarks[book_id]:
                self.create_bookmark_widget(dialog, bookmark)

    def create_bookmark_widget(self, parent, bookmark):
        """Create a widget for a bookmark."""
        frame = ctk.CTkFrame(parent, fg_color="#2F3F4F")
        frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            frame,
            text=f"Position: {int(bookmark['position'] * 100)}%",
            text_color="#FFFFFF"
        ).pack(pady=2)
        
        btn = ctk.CTkButton(
            frame,
            text="Go to Bookmark",
            fg_color="#3F4F5F",
            hover_color="#4F5F6F",
            command=lambda: self.go_to_bookmark(bookmark)
        )
        btn.pack(pady=5)

    def add_bookmark(self, dialog):
        """Add a bookmark at current position."""
        if not self.current_book:
            return
        
        book_id = self.current_book['id']
        if book_id not in self.bookmarks:
            self.bookmarks[book_id] = []
        
        bookmark = {
            'position': self.current_position,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.bookmarks[book_id].append(bookmark)
        self.save_bookmarks()
        
        # Update dialog
        self.create_bookmark_widget(dialog, bookmark)

    def go_to_bookmark(self, bookmark):
        """Go to bookmark position."""
        self.current_position = bookmark['position']
        self.update_progress()
        if self.is_playing:
            self.toggle_play()  # Stop current playback
            self.toggle_play()  # Start from new position

    def update_progress(self):
        """Update progress display."""
        if self.current_text:
            self.progress_bar.set(self.current_position)
            
            # Update time display (rough estimate)
            total_seconds = len(self.current_text) / (200 * self.playback_speed)  # ~200 chars per second
            current_seconds = total_seconds * self.current_position
            
            self.current_time.configure(text=self.format_time(current_seconds))
            self.total_time.configure(text=self.format_time(total_seconds))

    def format_time(self, seconds):
        """Format seconds to MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def update_library_list(self):
        """Update the library list display."""
        # Clear existing items
        for widget in self.book_list.winfo_children():
            widget.destroy()
        
        # Add books to list
        for book_id, book in self.library.items():
            # Create frame for book item
            book_frame = ctk.CTkFrame(self.book_list, fg_color="#2F3F4F")
            book_frame.pack(fill="x", padx=5, pady=2)
            
            # Book title
            title = ctk.CTkLabel(
                book_frame,
                text=book['title'],
                font=("Arial", 12),
                text_color="#FFFFFF"
            )
            title.pack(side="left", padx=10, pady=5)
            
            # Make the whole frame clickable
            book_frame.bind("<Button-1>", lambda e, id=book_id: self.load_book(id))
            title.bind("<Button-1>", lambda e, id=book_id: self.load_book(id))

    def load_book(self, book_id):
        """Load a book from the library."""
        if book_id in self.library:
            self.current_book = self.library[book_id]
            self.book_title.configure(text=self.current_book['title'])
            
            try:
                with open(self.current_book['path'], 'r', encoding='utf-8') as f:
                    self.current_text = f.read()
            except:
                with open(self.current_book['path'], 'rb') as f:
                    self.current_text = f.read().decode('utf-8', errors='ignore')
            
            self.current_position = 0
            self.update_progress()

    def add_book(self):
        """Add a new book to the library."""
        try:
            file_path = ctk.filedialog.askopenfilename(
                title="Select PDF Book",
                filetypes=[("PDF files", "*.pdf"), ("Text files", "*.txt")]
            )
            
            if file_path:
                # Generate unique book ID
                book_id = str(int(datetime.now().timestamp()))
                
                # Create book entry
                book = {
                    'id': book_id,
                    'title': os.path.splitext(os.path.basename(file_path))[0],
                    'path': file_path,
                    'last_played': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Read the text
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.current_text = f.read()
                except:
                    with open(file_path, 'rb') as f:
                        self.current_text = f.read().decode('utf-8', errors='ignore')
                
                # Add to library
                self.library[book_id] = book
                self.save_library()
                self.update_library_list()
                
                # Select the new book
                self.current_book = book
                self.book_title.configure(text=book['title'])
                self.current_position = 0
                self.update_progress()
                
        except Exception as e:
            print(f"Error adding book: {str(e)}")

    def load_library(self):
        """Load the library data from file."""
        try:
            if os.path.exists('library.json'):
                with open('library.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading library: {str(e)}")
        return {}

    def save_library(self):
        """Save the library data to file."""
        try:
            with open('library.json', 'w') as f:
                json.dump(self.library, f)
        except Exception as e:
            print(f"Error saving library: {str(e)}")

    def load_bookmarks(self):
        """Load bookmarks from file."""
        try:
            if os.path.exists('bookmarks.json'):
                with open('bookmarks.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading bookmarks: {str(e)}")
        return {}

    def save_bookmarks(self):
        """Save bookmarks to file."""
        try:
            with open('bookmarks.json', 'w') as f:
                json.dump(self.bookmarks, f)
        except Exception as e:
            print(f"Error saving bookmarks: {str(e)}")

    def get_last_played_book(self):
        """Get the most recently played book."""
        if not self.library:
            return None
        return max(self.library.values(), 
                  key=lambda x: x.get('last_played', ''), 
                  default=None)

    def show_resume_dialog(self, book):
        """Show dialog to resume last played book."""
        self.current_book = book
        self.book_title.configure(text=book['title'])
        
        try:
            with open(book['path'], 'r', encoding='utf-8') as f:
                self.current_text = f.read()
        except:
            with open(book['path'], 'rb') as f:
                self.current_text = f.read().decode('utf-8', errors='ignore')
        
        self.current_position = 0
        self.update_progress()

    def run(self):
        """Run the application."""
        self.app.mainloop()

if __name__ == "__main__":
    player = AudiobookPlayer()
    player.run() 