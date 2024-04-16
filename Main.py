import os
import random
import tkinter as tk
from tkinter import filedialog
from tkinter import *
import vlc

class Song:
    def __init__(self, path, priority=50):
        self.path = path
        self.priority = priority

class MusicPlayer:
    def __init__(self, root):
        self.playlist = []
        self.root = root
        self.last_dir = "/"
        self.file_dialog_open = False  # Flag to track if file dialog is open
        self.control_frame_visible = True  # Flag to track if the control frame is visible

        # Create frame for VLC video
        self.vlc_frame = tk.Frame(root)
        self.vlc_frame.grid(row=0, column=0, sticky="nsew")

        # VLC initialization
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.media_player.set_hwnd(self.vlc_frame.winfo_id())  # Set the window ID where VLC should render

        # Create frame for controls and playlist
        self.control_frame = tk.Frame(root)
        self.control_frame.grid(row=0, column=1, sticky="nsew")

        # Create a File Explorer label
        label = Label(self.control_frame, text='File Explorer', width=20, height=2, fg='blue')
        label.grid(row=0, column=0, padx=10, pady=10)

        # Creating a button to open the file explorer
        button_explore = Button(self.control_frame, text='Browse Files', command=self.browseFiles)
        button_explore.grid(row=1, column=0, padx=10, pady=10)

        # Creating a button to add a directory
        button_directory = Button(self.control_frame, text='Add Directory', command=self.addDirectory)
        button_directory.grid(row=2, column=0, padx=10, pady=10)

        # Creating a button to play the music
        self.button_play = Button(self.control_frame, text='Play Music', command=self.play_music)
        self.button_play.grid(row=3, column=0, padx=10, pady=10)

        # Creating a listbox to display the playlist
        self.listbox = Listbox(self.control_frame)
        self.listbox.grid(row=4, column=0, padx=10, pady=10)

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Bind mouse events to control frame visibility
        self.vlc_frame.bind("<Enter>", self.hide_control_frame)
        self.control_frame.bind("<Enter>", self.show_control_frame)
        self.vlc_frame.bind("<Leave>", self.show_control_frame)
        self.control_frame.bind("<Leave>", self.hide_control_frame)
        self.root.bind("<Motion>", self.handle_mouse_motion)

    def browseFiles(self, event=None):
        self.file_dialog_open = True  # Set flag to indicate file dialog is open
        filename = filedialog.askopenfilename(initialdir=self.last_dir, title="Select a File", filetypes=(("Text files", "*.mp4*"), ("all files", "*.*")))
        self.last_dir = os.path.dirname(filename)
        self.add_song(Song(filename, 50))
        self.file_dialog_open = False  # Reset flag after file dialog is closed

    def addDirectory(self, event=None):
        self.file_dialog_open = True
        directory = filedialog.askdirectory(initialdir=self.last_dir, title="Select a Directory")
        self.last_dir = directory
        for filename in os.listdir(directory):
            if filename.endswith(".mp4"):
                self.add_song(Song(os.path.join(directory, filename), 50))
        self.file_dialog_open = False

    def add_song(self, song):
        self.playlist.append(song)
        self.listbox.insert(END, os.path.basename(song.path))

    def play_music(self, event=None):
        if not self.playlist:
            print("Playlist is empty")
            return

        probabilities = [song.priority for song in self.playlist]
        total = sum(probabilities)
        probabilities = [p/total for p in probabilities]
        selected_song = random.choices(self.playlist, probabilities)[0]

        media = self.instance.media_new(selected_song.path)
        self.media_player.set_media(media)
        self.media_player.play()

    def hide_control_frame(self, event=None):
        if not self.file_dialog_open:
            self.control_frame.grid_forget()
            self.control_frame_visible = False

    def show_control_frame(self, event=None):
        if not self.control_frame_visible and not self.file_dialog_open:
            self.control_frame.grid(row=0, column=1, sticky="nsew")
            self.control_frame_visible = True

    def handle_mouse_motion(self, event):
        window_width = self.root.winfo_width()
        mouse_x = event.x_root - self.root.winfo_rootx()

        if mouse_x >= window_width - 10:  # Adjust this threshold as needed
            self.show_control_frame()

# Create the root window
root = Tk()
root.title('Music Player')
root.geometry("800x500")

# Create the MusicPlayer
player = MusicPlayer(root)

# Run the application
root.mainloop()
