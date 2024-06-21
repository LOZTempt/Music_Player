import os
import random
import tkinter as tk
from tkinter import filedialog, Scale, ttk
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
        self.file_dialog_open = False
        self.control_frame_visible = True
        self.current_song_index = -1
        self.full_screen = False
        self.cursor_position_unchanged_counter = 0
        self.previous_cursor_position = (-1, -1)
        self.video_loaded = False
        self.is_playing = False
        self.is_seeking = False

        # Frame for VLC video
        self.vlc_frame = tk.Frame(root, bg="black")
        self.vlc_frame.grid(row=0, column=0, sticky="nsew")

        # Control frame for playlist and file operations
        self.control_frame = tk.Frame(root)
        self.control_frame.place(x=650, y=0, width=150, relheight=1)

        # Frame for media controls below the VLC frame
        self.media_controls = tk.Frame(root)
        self.media_controls.grid(row=1, column=0, sticky="ew") 

        # You can adjust pane height here, assuming you want the whole media_controls frame to conform to 60 pixels.
        self.media_controls.configure(height=60)
        # If you are using a fixed size for the media_controls frame, use self.media_controls.place() instead of grid().
        # self.media_controls.place(x=0, y=0, relwidth=1, height=60)

        # VLC initialization
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        root.after(0, self.set_vlc_window)

        # File explorer label and buttons
        label = Label(self.control_frame, text='File Explorer', width=20, height=2, fg='blue')
        label.grid(row=0, column=0, padx=10, pady=10)

        button_explore = Button(self.control_frame, text='Browse Files', command=self.browseFiles)
        button_explore.grid(row=1, column=0, padx=10, pady=10)

        button_directory = Button(self.control_frame, text='Add Directory', command=self.addDirectory)
        button_directory.grid(row=2, column=0, padx=10, pady=10)

        self.button_play = Button(self.control_frame, text='Play Music', command=self.play_music)
        self.button_play.grid(row=3, column=0, padx=10, pady=10)

        self.listbox = Listbox(self.control_frame)
        self.listbox.grid(row=4, column=0, padx=10, pady=10)

        # Media control buttons using grid layout
        self.button_prev_track = Button(self.media_controls, text='<< Previous', command=self.prev_track)
        self.button_prev_track.grid(row=1, column=0, padx=5, pady=2)

        self.button_rewind = Button(self.media_controls, text='<< Rewind', command=self.rewind)
        self.button_rewind.grid(row=1, column=1, padx=5, pady=2)

        self.button_play_pause = Button(self.media_controls, text='Play', command=self.toggle_play_pause)
        self.button_play_pause.grid(row=1, column=2, padx=5, pady=2)

        self.button_forward = Button(self.media_controls, text='Fast Forward >>', command=self.fast_forward)
        self.button_forward.grid(row=1, column=3, padx=5, pady=2)

        self.button_next_track = Button(self.media_controls, text='Next >>', command=self.next_track)
        self.button_next_track.grid(row=1, column=4, padx=5, pady=2)

        self.button_stop = Button(self.media_controls, text='Stop', command=self.stop)
        self.button_stop.grid(row=1, column=5, padx=5, pady=2)

        # Volume control slider
        self.volume_control = Scale(self.media_controls, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_control.set(60)
        self.volume_control.grid(row=1, column=6, padx=5, pady=2)

        # Seek bar above the buttons - remove labels and reduce padding
        style = ttk.Style()
        style.configure("TScale", sliderrelief='flat', background='white')

        self.seek_bar = Scale(self.media_controls, from_=0, to=100, orient=tk.HORIZONTAL, length=200,
                              command=self.seek, showvalue=0, sliderlength=10)
        self.seek_bar.grid(row=0, column=0, columnspan=7, sticky="ew", padx=0, pady=0)

        # Time labels within the media controls frame
        self.current_time_label = Label(self.media_controls, text="0:00", bg='black', fg='white')
        self.current_time_label.grid(row=1, column=7, padx=(5, 0), pady=2)

        # Bindings for seek bar
        self.seek_bar.bind("<Button-1>", self.on_seek_start)
        self.seek_bar.bind("<ButtonRelease-1>", self.on_seek_end)

        # Root and frame configurations
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)
        self.root.bind('<Configure>', self.adjust_elements)
        self.vlc_frame.bind("<Configure>", self.update_vlc_window_size)

        # Timer for hiding controls and other initializations
        self.hide_controls_timer = None
        self.poll_mouse_position()
        self.update_seek_bar()

    def adjust_elements(self, event=None):
        video_aspect_ratio = 16 / 9
        window_width = self.root.winfo_width() - 150
        window_height = self.root.winfo_height() - 50

        if window_width / window_height > video_aspect_ratio:
            video_height = window_height
            video_width = int(video_height * video_aspect_ratio)
        else:
            video_width = window_width
            video_height = int(video_width / video_aspect_ratio)

        self.vlc_frame.grid(row=0, column=0, sticky="nsew", ipadx=int((self.root.winfo_width() - 150 - video_width) / 2), ipady=int((self.root.winfo_height() - 50 - video_height) / 2))
        self.update_vlc_window_size()

    def update_vlc_window_size(self, event=None):
        self.set_vlc_window()

    def set_vlc_window(self):
        if os.name == "nt":
            self.media_player.set_hwnd(self.vlc_frame.winfo_id())
        else:
            self.media_player.set_xwindow(self.vlc_frame.winfo_id())

    def browseFiles(self, event=None):
        self.file_dialog_open = True
        filename = filedialog.askopenfilename(initialdir=self.last_dir, title="Select a File", filetypes=(("Text files", "*.mp4*"), ("all files", "*.*")))
        self.last_dir = os.path.dirname(filename)
        self.add_song(Song(filename, 50))
        self.file_dialog_open = False

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

        self.current_song_index = self.playlist.index(selected_song)

        media = self.instance.media_new(selected_song.path)
        self.media_player.set_media(media)
        self.media_player.play()
        self.button_play_pause.config(text="Pause")
        self.video_loaded = True

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
        self.video_loaded = True

    def set_volume(self, volume):
        self.media_player.audio_set_volume(int(volume))

    def stop(self):
        self.media_player.stop()
        self.video_loaded = False

    def seek(self, value):
        if self.video_loaded and self.is_seeking:
            duration = self.media_player.get_length() / 1000
            new_time = int(duration * (int(value) / 100))
            self.media_player.set_time(new_time * 1000)

    def update_seek_bar(self):
        if self.media_player.is_playing():
            duration = self.media_player.get_length() / 1000
            current_time = self.media_player.get_time() / 1000

            current_time_str = self.format_time(current_time)
            total_time_str = self.format_time(duration)
            self.current_time_label.config(text=f"{current_time_str} / {total_time_str}")

            if duration > 0:
                seek_value = int((current_time / duration) * 100)
                
                # Temporarily remove the command to avoid triggering the seek method
                self.seek_bar.config(command="")
                self.seek_bar.set(seek_value)
                self.seek_bar.config(command=self.seek)

        self.root.after(1000, self.update_seek_bar)

    def format_time(self, total_seconds):
        hours = int(total_seconds / 3600)
        minutes = int((total_seconds % 3600) / 60)
        seconds = int(total_seconds % 60)
        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    
    def on_seek_start(self, event):
        self.is_seeking = True

    def on_seek_end(self, event):
        self.is_seeking = False
        # Ensure that the seek method is called once after the user finishes seeking
        self.seek(self.seek_bar.get())

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
        self.media_controls.place(relx=0, rely=1, anchor="sw", relwidth=1, height=60)

    def poll_mouse_position(self):
        mouse_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        mouse_y = self.root.winfo_pointery() - self.root.winfo_rooty()

        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()

        cursor_position = self.media_player.video_get_cursor()

        if self.video_loaded:
            if cursor_position == self.previous_cursor_position:
                self.cursor_position_unchanged_counter += 1
            else:
                self.cursor_position_unchanged_counter = 0

            self.previous_cursor_position = cursor_position

            if 0 <= mouse_x < window_width and 0 <= mouse_y < window_height:
                if self.cursor_position_unchanged_counter >= 40 and not mouse_y >= window_height - 50:
                    self.hide_controls()
                elif not self.media_controls.winfo_ismapped():
                    self.show_controls()
            else:
                self.hide_controls()

            if 0 <= mouse_x < window_width and 0 <= mouse_y < window_height:
                if mouse_x >= window_width - 100:
                    self.show_control_frame()
                else:
                    self.hide_control_frame()
            else:
                self.hide_control_frame()

        elif not self.is_playing:
            self.cursor_position_unchanged_counter = 0
            self.show_controls()
            self.show_control_frame()

        self.root.after(100, self.poll_mouse_position)

root = Tk()
root.title('Music Player')
root.geometry("800x500")

player = MusicPlayer(root)

root.mainloop()
