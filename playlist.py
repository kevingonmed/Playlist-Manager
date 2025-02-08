from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
import datetime

# Create a MongoDB client instance
client = MongoClient("mongodb://localhost:27017/")  # If you are using a local connection

try:
    # Execute the ping command to check the connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")

    db = client["playlist"]  # Access the "playlist" database
    
    # Access the "songs" and "playlists" collections
    songs_collection = db["songs"]
    playlist_collection = db["playlists"]
    counters_collection = db["counters"]  # Collection to keep track of ID counters

    # Initialize the counter if it doesn't exist
    if counters_collection.count_documents({"_id": "song_id"}) == 0:
        counters_collection.insert_one({"_id": "song_id", "seq": 0})
    if counters_collection.count_documents({"_id": "playlist_id"}) == 0:
        counters_collection.insert_one({"_id": "playlist_id", "seq": 0})

    # Function to get the next sequential ID
    def get_next_sequence_id(counter_name):
        counter = counters_collection.find_one_and_update(
            {"_id": counter_name},
            {"$inc": {"seq": 1}},
            return_document=True
        )
        return counter["seq"]

    # Function to create a new playlist
    def new_playlist():
        name = input("Enter the name of the playlist: ")
        songs = []  # Initially, the song list will be empty
        created_at = datetime.datetime.now()
        updated_at = datetime.datetime.now()

        # Get the next sequential ID
        playlist_id = get_next_sequence_id("playlist_id")

        playlist = {
            "_id": playlist_id,
            "name": name,
            "songs": songs,
            "created_at": created_at,
            "updated_at": updated_at
        }

        playlist_collection.insert_one(playlist)
        print(f"Playlist created successfully! ID: {playlist_id}")

    # Function to add a song to a playlist
    def add_song(playlist_id):
        # Song details
        title = input("Enter the song title: ")
        artist = input("Enter the artist: ")
        album = input("Enter the album: ")
        genre = input("Enter the genre: ")
        duration = input("Enter the song duration (e.g., '3:53'): ")

        # Get the next sequential ID for the song
        song_id = get_next_sequence_id("song_id")

        # Create the song document
        song = {
            "_id": song_id,
            "title": title,
            "artist": artist,
            "album": album,
            "genre": genre,
            "duration": duration
        }
        
        # Insert the song into the 'songs' collection
        songs_collection.insert_one(song)
        
        # Update the playlist by adding the song ID
        playlist_collection.update_one(
            {"_id": playlist_id}, 
            {"$push": {"songs": song_id}}  # Add the song ID to the song list
        )
        
        print(f"Song successfully added to the playlist! Song ID: {song_id}")

    # Function to remove a song from a playlist
    def remove_song(playlist_id, song_id):
        songs_collection.delete_one({"_id": song_id})  # Remove the song from the 'songs' collection
        
        # Update the playlist by removing the song ID from the song list
        playlist_collection.update_one(
            {"_id": playlist_id}, 
            {"$pull": {"songs": song_id}}  # Remove the song ID from the song list
        )
        
        print("Song successfully removed from the playlist!")

    # Function to remove a playlist
    def remove_playlist(playlist_id):
        playlist_collection.delete_one({"_id": playlist_id})  # Remove the playlist
        print("Playlist successfully removed!")

    # Function to display a playlist
    def display_playlist(playlist_id):
        playlist = playlist_collection.find_one({"_id": playlist_id})
        
        print("Playlist information:")
        print(f"Name: {playlist['name']}")
        print("Songs:")
        
        for song_id in playlist['songs']:
            song = songs_collection.find_one({"_id": song_id})
            print(f"- {song['title']} by {song['artist']} ({song['album']}, {song['duration']})")
        
        print(f"Creation date: {playlist['created_at']}")
        print(f"Last update date: {playlist['updated_at']}")

except PyMongoError as e:  # Handle connection errors
    print(f"Error: Could not connect to MongoDB. Details: {e}")


# Menu options for the user
print("Welcome to the song playlist")
while True:
    print("\n1: View my playlists")
    print("2: Add a new playlist")
    print("3: Add a song to a playlist")
    print("4: Remove a song from a playlist")
    print("5: Remove a playlist")
    print("6: Display the Playlist")
    print("7: Exit")
    
    try:
        x = int(input("What would you like to do? "))
        
        if x == 1:
            playlists = playlist_collection.find()  # Show all playlists
            for playlist in playlists:
                print(f"{playlist['_id']} - {playlist['name']}")
        
        elif x == 2:
            new_playlist()
        
        elif x == 3:
            playlist_id = int(input("Enter the ID of the playlist you want to add a song to: "))
            add_song(playlist_id)
        
        elif x == 4:
            playlist_id = int(input("Enter the ID of the playlist you want to remove a song from: "))
            song_id = int(input("Enter the ID of the song to remove: "))
            remove_song(playlist_id, song_id)
        
        elif x == 5:
            playlist_id = int(input("Enter the ID of the playlist to delete: "))
            remove_playlist(playlist_id)

        elif x == 6:
            playlist_id = int(input("Enter the ID of the playlist to view the songs: "))
            display_playlist(playlist_id)

        
        elif x == 7:
            print("Goodbye!")
            break
        
        else:
            print("Invalid option. Try again.")
    
    except ValueError:
        print("Please enter a valid number.")
