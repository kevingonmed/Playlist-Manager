import tkinter as tk
from tkinter import messagebox
from pymongo import MongoClient
import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# MongoDB client initialization
client = MongoClient("mongodb://localhost:27017/")  # If you are using a local connection
db = client["playlist"]  # Access the "playlist" database
songs_collection = db["songs"]
playlist_collection = db["playlists"]
counters_collection = db["counters"]  # Collection to keep track of ID counters

# Spotify API initialization
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="bea29ba6a3414542b5ef127c8d5508d5",
                                               client_secret="4730ffcf147748a3bfc563406aab8af5",
                                               redirect_uri="http://localhost:8888/callback",
                                               scope=["user-library-read", "playlist-read-private", "playlist-modify-private", "playlist-modify-public"]))


# Function for creating a new playlist
def new_playlist():
    name = name_entry.get()
    if name == "":
        messagebox.showwarning("Input Error", "Please enter a playlist name.")
        return
    
    created_at = datetime.datetime.now()
    updated_at = datetime.datetime.now()
    playlist_id = get_next_sequence_id("playlist_id")
    
    playlist = {
        "_id": playlist_id,
        "name": name,
        "songs": [],
        "created_at": created_at,
        "updated_at": updated_at
    }
    
    playlist_collection.insert_one(playlist)
    messagebox.showinfo("Success", f"Playlist created successfully! ID: {playlist_id}")


# Function to get the next sequence ID
def get_next_sequence_id(counter_name):
    counter = counters_collection.find_one_and_update(
        {"_id": counter_name},
        {"$inc": {"seq": 1}},
        return_document=True
    )
    return counter["seq"]


# Function to add a song to a playlist and MongoDB
def add_song_to_playlist():
    selected_song_index = result_list.curselection()  # Get the selected song index
    if not selected_song_index:
        messagebox.showwarning("Selection Error", "Please select a song.")
        return

    selected_song = result_list.get(selected_song_index[0])  # Get the selected song
    song_name, artist_name = selected_song.split(" - ")  # Split song name and artist
    
    # Search for the song on Spotify
    result = sp.search(q=f"{song_name} {artist_name}", limit=1, type='track')
    
    # Check if the search returned any result
    if not result['tracks']['items']:
        messagebox.showwarning("Song Not Found", "No song found matching that title.")
        return
    
    # We have results, so let's extract the first track
    track = result['tracks']['items'][0]
    track_id = track['id']
    track_name = track['name']  # The actual name of the track in Spotify
    track_artist = track['artists'][0]['name']  # The artist's name from the first artist
    track_uri = track['uri']  # The URI of the track (Spotify's internal identifier)

    print(f"Found track: {track_name} by {track_artist} (ID: {track_id}, URI: {track_uri})")
    
    # Add song to Spotify playlist
    playlist_id = playlist_id_entry.get()  # Get the playlist ID
    sp.playlist_add_items(playlist_id, [track_id])  # Add the song to the playlist
    
    # Prepare song data to insert into MongoDB
    song_data = {
        "name": track_name,  # Using track_name from Spotify
        "artist": track_artist,  # Using artist_name from Spotify
        "track_id": track_id,  # Using the track_id from Spotify
        "uri": track_uri,  # Store the URI for easy reference
        "added_at": datetime.datetime.now(),
        "playlist_id": playlist_id
    }

    try:
        # Insert the song into the "songs" collection in MongoDB
        result = songs_collection.insert_one(song_data)
        if result.inserted_id:
            print(f"Song inserted successfully into MongoDB with ID: {result.inserted_id}")
        else:
            print("Failed to insert the song into MongoDB.")
        
        # After inserting the song into the "songs" collection, update the playlist
        playlist_update = playlist_collection.update_one(
            {"_id": int(playlist_id)},  # Find the playlist by its ID
            {"$push": {"songs": song_data}}  # Push the new song to the 'songs' array
        )

        if playlist_update.modified_count > 0:
            print(f"Playlist {playlist_id} updated successfully with the new song.")
        else:
            print(f"Failed to update playlist {playlist_id}.")

    except Exception as e:
        print(f"Error inserting song into MongoDB: {e}")
        messagebox.showerror("Database Error", f"An error occurred while inserting the song into the database: {e}")
    
    # Show success message
    messagebox.showinfo("Success", f"Song '{track_name}' by {track_artist} added to playlist and saved to MongoDB!")


# Function to show user playlists
def show_playlists():
    playlists = sp.current_user_playlists()['items']  # Get user playlists
    playlists_list.delete(0, tk.END)  # Clear existing list
    for playlist in playlists:
        playlists_list.insert(tk.END, playlist['name'])  # Insert playlist name


# Function to search for a song on Spotify
def search_song():
    track_name = song_name_entry.get()  # Get the song name from the entry
    if track_name == "":
        messagebox.showwarning("Input Error", "Please enter a song title.")
        return
    
    result = sp.search(q=track_name, limit=5, type='track')  # Limit to 5 results
    if not result['tracks']['items']:
        messagebox.showwarning("Song Not Found", "No song found matching that title.")
        return

    result_list.delete(0, tk.END)  # Clear previous results
    for track in result['tracks']['items']:
        result_list.insert(tk.END, f"{track['name']} - {track['artists'][0]['name']}")  # Insert song name and artist


# Main GUI window
window = tk.Tk()
window.title("Music Playlist Manager")
window.geometry("600x600")

# Playlist section
playlist_label = tk.Label(window, text="Create a New Playlist")
playlist_label.pack()

name_label = tk.Label(window, text="Enter Playlist Name:")
name_label.pack()
name_entry = tk.Entry(window)
name_entry.pack()

create_playlist_button = tk.Button(window, text="Create Playlist", command=new_playlist)
create_playlist_button.pack()

# Add song section
song_label = tk.Label(window, text="Add a Song to Playlist")
song_label.pack()

playlist_id_label = tk.Label(window, text="Enter Playlist ID:")
playlist_id_label.pack()
playlist_id_entry = tk.Entry(window)
playlist_id_entry.pack()

song_name_label = tk.Label(window, text="Enter Song Title:")
song_name_label.pack()
song_name_entry = tk.Entry(window)
song_name_entry.pack()

search_button = tk.Button(window, text="Search Song", command=search_song)
search_button.pack()

# Show search results
result_list = tk.Listbox(window)
result_list.pack()

add_song_button = tk.Button(window, text="Add Song to Playlist", command=add_song_to_playlist)
add_song_button.pack()

# Display user playlists
show_playlists_button = tk.Button(window, text="Show My Playlists", command=show_playlists)
show_playlists_button.pack()

playlists_list = tk.Listbox(window)
playlists_list.pack()

# Run the GUI
window.mainloop()
