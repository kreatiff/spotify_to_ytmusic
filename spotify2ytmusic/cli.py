#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
import pprint

from . import backend


def list_liked_albums():
    """
    List albums that have been liked.
    """
    for song in backend.iter_spotify_liked_albums():
        print(f"{song.album} - {song.artist} - {song.title}")


def list_playlists():
    """
    List the playlists on Spotify and YTMusic
    """
    yt = backend.get_ytmusic()

    spotify_pls = backend.load_playlists_json()

    #  Liked music
    print("== Spotify")
    for src_pl in spotify_pls["playlists"]:
        print(
            f"{src_pl.get('id')} - {src_pl['name']:50} ({len(src_pl['tracks'])} tracks)"
        )

    print()
    print("== YTMusic")
    for pl in yt.get_library_playlists(limit=5000):
        print(f"{pl['playlistId']} - {pl['title']:40} ({pl.get('count', '?')} tracks)")


def create_playlist():
    """
    Create a YTMusic playlist
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--privacy",
            default="PRIVATE",
            help="The privacy seting of created playlists (PRIVATE, PUBLIC, UNLISTED, default PRIVATE)",
        )
        parser.add_argument(
            "playlist_name",
            type=str,
            help="Name of playlist to create.",
        )

        return parser.parse_args()

    args = parse_arguments()

    backend.create_playlist(args.playlist_name, privacy_status=args.privacy)


def search():
    """Search for a track on ytmusic"""

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "track_name",
            type=str,
            help="Name of track to search for",
        )
        parser.add_argument(
            "--artist",
            type=str,
            help="Artist to look up",
        )
        parser.add_argument(
            "--album",
            type=str,
            help="Album name",
        )
        parser.add_argument(
            "--algo",
            type=int,
            default=0,
            help="Algorithm to use for search (0 = exact, 1 = extended, 2 = approximate)",
        )
        return parser.parse_args()

    args = parse_arguments()

    yt = backend.get_ytmusic()
    details = backend.ResearchDetails()
    ret = backend.lookup_song(
        yt, args.track_name, args.artist, args.album, args.algo, details=details
    )

    print(f"Query: '{details.query}'")
    print("Selected song:")
    pprint.pprint(ret)
    print()
    print(f"Search Suggestions: '{details.suggestions}'")
    if details.songs:
        print("Top 5 songs returned from search:")
        for song in details.songs[:5]:
            pprint.pprint(song)


def load_liked_albums():
    """
    Load the "Liked" albums from Spotify into YTMusic.  Spotify stores liked albums separately
    from liked songs, so "load_liked" does not see the albums, you instead need to use this.
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )
        parser.add_argument(
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )
        parser.add_argument(
            "--algo",
            type=int,
            default=0,
            help="Algorithm to use for search (0 = exact, 1 = extended, 2 = approximate)",
        )

        return parser.parse_args()

    args = parse_arguments()

    spotify_pls = backend.load_playlists_json()

    backend.copier(
        backend.iter_spotify_liked_albums(
            spotify_encoding=args.spotify_playlists_encoding
        ),
        None,
        args.dry_run,
        args.track_sleep,
        args.algo,
    )


def load_liked():
    """
    Load the "Liked Songs" playlist from Spotify into YTMusic.
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )
        parser.add_argument(
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )
        parser.add_argument(
            "--algo",
            type=int,
            default=0,
            help="Algorithm to use for search (0 = exact, 1 = extended, 2 = approximate)",
        )
        parser.add_argument(
            "--reverse-playlist",
            action="store_true",
            help="Reverse playlist on load, normally this is not set for liked songs as "
            "they are added in the opposite order from other commands in this program.",
        )

        return parser.parse_args()

    args = parse_arguments()

    backend.copier(
        backend.iter_spotify_playlist(
            None,
            spotify_encoding=args.spotify_playlists_encoding,
            reverse_playlist=args.reverse_playlist,
        ),
        None,
        args.dry_run,
        args.track_sleep,
        args.algo,
    )


def load_from_json():
    """
    Load songs from a simple JSON metadata file.
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON metadata file",
        )
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )
        parser.add_argument(
            "--algo",
            type=int,
            default=0,
            help="Algorithm to use for search (0 = exact, 1 = extended, 2 = approximate)",
        )
        return parser.parse_args()

    args = parse_arguments()

    backend.copier(
        backend.iter_metadata_json(args.json_file),
        None,
        args.dry_run,
        args.track_sleep,
        args.algo,
    )


def load_from_urls():
    """
    Load songs from a JSON file of Spotify track URLs.
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON file containing Spotify URLs",
        )
        parser.add_argument(
            "--client-id",
            type=str,
            help="Spotify Client ID",
        )
        parser.add_argument(
            "--client-secret",
            type=str,
            help="Spotify Client Secret",
        )
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )
        parser.add_argument(
            "--algo",
            type=int,
            default=0,
            help="Algorithm to use for search (0 = exact, 1 = extended, 2 = approximate)",
        )
        return parser.parse_args()

    args = parse_arguments()

    client_id = args.client_id
    client_secret = args.client_secret

    if not client_id or not client_secret:
        import os
        client_id = client_id or os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = client_secret or os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("ERROR: Spotify Client ID and Secret are required for this command.")
        print("       Provide them via --client-id/--client-secret or SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET env vars.")
        sys.exit(1)

    backend.copier(
        backend.iter_spotify_urls(args.json_file, client_id, client_secret),
        None,
        args.dry_run,
        args.track_sleep,
        args.algo,
    )


def copy_playlist():
    """
    Copy a Spotify playlist to a YTMusic playlist
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )
        parser.add_argument(
            "spotify_playlist_id",
            type=str,
            help="ID of the Spotify playlist to copy from",
        )
        parser.add_argument(
            "ytmusic_playlist_id",
            type=str,
            help="ID of the YTMusic playlist to copy to.  If this argument starts with a '+', it is asumed to be the playlist title rather than playlist ID, and if a playlist of that name is not found, it will be created (without the +).  Example: '+My Favorite Blues'.  NOTE: The shell will require you to quote the name if it contains spaces.",
        )
        parser.add_argument(
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )
        parser.add_argument(
            "--algo",
            type=int,
            default=0,
            help="Algorithm to use for search (0 = exact, 1 = extended, 2 = approximate)",
        )
        parser.add_argument(
            "--no-reverse-playlist",
            action="store_true",
            help="Do not reverse playlist on load, regular playlists are reversed normally "
            "so they end up in the same order as on Spotify.",
        )
        parser.add_argument(
            "--privacy",
            default="PRIVATE",
            help="The privacy seting of created playlists (PRIVATE, PUBLIC, UNLISTED, default PRIVATE)",
        )

        return parser.parse_args()

    args = parse_arguments()
    backend.copy_playlist(
        spotify_playlist_id=args.spotify_playlist_id,
        ytmusic_playlist_id=args.ytmusic_playlist_id,
        track_sleep=args.track_sleep,
        dry_run=args.dry_run,
        spotify_playlists_encoding=args.spotify_playlists_encoding,
        reverse_playlist=not args.no_reverse_playlist,
        privacy_status=args.privacy,
    )


def copy_all_playlists():
    """
    Copy all Spotify playlists (except Liked Songs) to YTMusic playlists
    """

    def parse_arguments():
        parser = ArgumentParser()
        parser.add_argument(
            "--track-sleep",
            type=float,
            default=0.1,
            help="Time to sleep between each track that is added (default: 0.1)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not add songs to destination playlist (default: False)",
        )
        parser.add_argument(
            "--spotify-playlists-encoding",
            default="utf-8",
            help="The encoding of the `playlists.json` file.",
        )
        parser.add_argument(
            "--algo",
            type=int,
            default=0,
            help="Algorithm to use for search (0 = exact, 1 = extended, 2 = approximate)",
        )
        parser.add_argument(
            "--no-reverse-playlist",
            action="store_true",
            help="Do not reverse playlist on load, regular playlists are reversed normally "
            "so they end up in the same order as on Spotify.",
        )
        parser.add_argument(
            "--privacy",
            default="PRIVATE",
            help="The privacy seting of created playlists (PRIVATE, PUBLIC, UNLISTED, default PRIVATE)",
        )

        return parser.parse_args()

    args = parse_arguments()
    backend.copy_all_playlists(
        track_sleep=args.track_sleep,
        dry_run=args.dry_run,
        spotify_playlists_encoding=args.spotify_playlists_encoding,
        reverse_playlist=not args.no_reverse_playlist,
        privacy_status=args.privacy,
    )


def gui():
    """
    Run the Spotify2YTMusic GUI.
    """
    from . import gui

    gui.main()


def ytoauth():
    """
    Run the "ytmusicapi oauth" login.
    """
    from ytmusicapi.setup import main

    sys.argv = ["ytmusicapi", "oauth"]
    sys.exit(main())
