import os
import random
import tkinter as tk
from tkinter import filedialog, Scale
from tkinter import *
import vlc

#TODO add a counter (can be true/false) just to keep track of the first instance of a video being played so that both panes won't always appear when the video is paused
# also as an extension or an alternate solution see if there is another better vlc function for this or make the player pause/play button work differently 
# make the play button on the right pane be either play or stop and set a T/F variable to show/hide the panes based on that! ie: true means video is playing and don't always show the panes and vice versa

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
        self.control_frame_visible = True  # Start with the control frame visible
        self.current_song_index = -1  # Track the current song index
        self.full_screen = False  # Flag to track full screen state
        self.cursor_position_unchanged_counter = 0
        self.previous_cursor_position = (-1, -1)  # Initialize previous cursor position
        self.video_loaded = False  # Flag to track if a video is loaded
        self.is_playing = False  # Flag to track if the video is currently playing

        # Create frame for VLC video
        self.vlc_frame = tk.Frame(root, bg="black")  # Background black to match video
        self.vlc_frame.grid(row=0, column=0, sticky="nsew")

        # Create frame for controls and playlist
        self.control_frame = tk.Frame(root)
        self.control_frame.place(x=650, y=0, width=150, relheight=1)  # Fixed size control panel

        # Create frame for media controls directly below the VLC frame
        self.media_controls = tk.Frame(root)
        self.media_controls.place(relx=0, rely=1, anchor="sw", relwidth=1, height=50)  # Snapped to the bottom

        # VLC initialization
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        root.after(0, self.set_vlc_window)

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

        # Adding control buttons
        self.button_rewind = Button(self.media_controls, text='<< Rewind', command=self.rewind)
        self.button_rewind.grid(row=0, column=0, padx=5)

        self.button_play_pause = Button(self.media_controls, text='Play', command=self.toggle_play_pause)
        self.button_play_pause.grid(row=0, column=1, padx=5)

        self.button_forward = Button(self.media_controls, text='Fast Forward >>', command=self.fast_forward)
        self.button_forward.grid(row=0, column=2, padx=5)

        self.button_prev_track = Button(self.media_controls, text='<< Previous', command=self.prev_track)
        self.button_prev_track.grid(row=0, column=3, padx=5)

        self.button_next_track = Button(self.media_controls, text='Next >>', command=self.next_track)
        self.button_next_track.grid(row=0, column=4, padx=5)

        # Adding a volume control
        self.volume_control = Scale(self.media_controls, from_=0, to=100, orient=HORIZONTAL, command=self.set_volume)
        self.volume_control.set(60)  # Set default volume to 50%
        self.volume_control.grid(row=0, column=5, padx=5)

        # Adding a stop button
        self.button_stop = Button(self.media_controls, text='Stop', command=self.stop)
        self.button_stop.grid(row=0, column=6, padx=5)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        self.root.bind('<Configure>', self.adjust_elements)
        self.vlc_frame.bind("<Configure>", self.update_vlc_window_size)

        # Timer for hiding controls
        self.hide_controls_timer = None

        # Start polling for mouse position
        self.poll_mouse_position()

    def adjust_elements(self, event=None):
        # Maintain aspect ratio for the video
        video_aspect_ratio = 16 / 9  # Adjust this as per your requirement
        window_width = self.root.winfo_width() - 150  # Subtract control frame width
        window_height = self.root.winfo_height() - 50  # Subtract media controls height

        if window_width / window_height > video_aspect_ratio:
            # Window is wider relative to its height
            video_height = window_height
            video_width = int(video_height * video_aspect_ratio)
        else:
            # Window is taller relative to its width
            video_width = window_width
            video_height = int(video_width / video_aspect_ratio)

        # Adjust the vlc_frame size based on the aspect ratio
        self.vlc_frame.grid(row=0, column=0, sticky="nsew", ipadx=int((self.root.winfo_width() - 150 - video_width) / 2), ipady=int((self.root.winfo_height() - 50 - video_height) / 2))

        # Ensure VLC resizes correctly
        self.update_vlc_window_size()

    def update_vlc_window_size(self, event=None):
        self.set_vlc_window()

    def set_vlc_window(self):
        # Ensure the media player is aware of the correct window handle
        if os.name == "nt":  # For Windows
            self.media_player.set_hwnd(self.vlc_frame.winfo_id())
        else:  # For other OSes
            self.media_player.set_xwindow(self.vlc_frame.winfo_id())

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

        self.current_song_index = self.playlist.index(selected_song)  # Update current song index

        media = self.instance.media_new(selected_song.path)
        self.media_player.set_media(media)
        self.media_player.play()
        self.button_play_pause.config(text="Pause")
        self.video_loaded = True  # Set flag to indicate video is loaded

    def toggle_play_pause(self):
        if self.media_player.is_playing():
            self.media_player.pause()
            self.button_play_pause.config(text="Play")
            self.is_playing = False
        else:
            self.media_player.play()
            self.button_play_pause.config(text="Pause")
            self.is_playing = True

    def rewind(self):
        current_time = self.media_player.get_time()
        self.media_player.set_time(max(0, current_time - 5000))

    def fast_forward(self):
        current_time = self.media_player.get_time()
        self.media_player.set_time(current_time + 5000)

    def prev_track(self):
        if self.playlist and self.current_song_index > 0:
            self.current_song_index -= 1
            self.play_selected_song()

    def next_track(self):
        if self.playlist and self.current_song_index < len(self.playlist) - 1:
            self.current_song_index += 1
            self.play_selected_song()

    def play_selected_song(self):
        selected_song = self.playlist[self.current_song_index]
        media = self.instance.media_new(selected_song.path)
        self.media_player.set_media(media)
        self.media_player.play()
        self.button_play_pause.config(text="Pause")
        self.video_loaded = True  # Set flag to indicate video is loaded

    def set_volume(self, volume):
        self.media_player.audio_set_volume(int(volume))

    def stop(self):
        self.media_player.stop()
        self.video_loaded = False  # Reset flag to indicate video is unloaded

    def hide_control_frame(self):
       if self.control_frame_visible:
           self.control_frame.place_forget()
           self.control_frame_visible = False

    def show_control_frame(self, event=None):
       if not self.control_frame_visible and not self.file_dialog_open:
           window_width = self.root.winfo_width() - 150
           self.control_frame.place(x=window_width, y=0, width=150, relheight=1)
           self.control_frame_visible = True

    def hide_controls(self):
        self.media_controls.place_forget()
        self.hide_controls_timer = None

    def show_controls(self, event=None):
        self.media_controls.place(relx=0, rely=1, anchor="sw", relwidth=1, height=50)

    def poll_mouse_position(self):
        # Get the mouse position relative to the root window
        mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        mouse_y = self.root.winfo_pointery() - self.root.winfo_rooty()

        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        # Get the mouse position relative to the VLC video area
        cursor_position = self.media_player.video_get_cursor()

        if self.video_loaded :
            # Check if the cursor position is the same as the previous position
            if cursor_position == self.previous_cursor_position:
                self.cursor_position_unchanged_counter += 1
            else:
                self.cursor_position_unchanged_counter = 0

            self.previous_cursor_position = cursor_position
            
            if 0 <= mouse_x < window_width and 0 <= mouse_y < window_height:
                # If the cursor position is unchanged for 40 checks (4 seconds) and the mouse is not over the controls, hide the controls
                if self.cursor_position_unchanged_counter >= 40 and not mouse_y >= window_height - 50:
                    self.hide_controls()
                elif not self.media_controls.winfo_ismapped(): # Only show controls if not visible already
                    self.show_controls()
            else:
                self.hide_controls()
            # Check if mouse is within window bounds
            if 0 <= mouse_x < window_width and 0 <= mouse_y < window_height:
                # Check if mouse is near the right edge for context menu visibility
                if mouse_x >= window_width - 100:
                    self.show_control_frame()
                else:
                    self.hide_control_frame()
            else:
                self.hide_control_frame()

        elif not self.is_playing:
            # Reset the counter and make sure the controls are visible while the video is not playing
            self.cursor_position_unchanged_counter = 0
            self.show_controls()
            self.show_control_frame()

        # Schedule the next poll
        self.root.after(100, self.poll_mouse_position)

# Create the root window
root = Tk()
root.title('Music Player')
root.geometry("800x500")

# Create the MusicPlayer
player = MusicPlayer(root)

# Run the application
root.mainloop()
