from django.conf import settings


import spotify
import threading

class SpotifyHandler():

    playlists = None
    instance = None

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = SpotifyHandler()

        return cls.instance

    def __init__(self):
        self.logged_in_event = threading.Event()
        self.session = spotify.Session()
        loop = spotify.EventLoop(self.session)
        loop.start()
        self.session.on(spotify.SessionEvent.CONNECTION_STATE_UPDATED, self.login_listener)

        self.session.login(settings.SPOTIFY_USER, settings.SPOTIFY_PASSWORD)

        self.logged_in_event.wait()

        assert(self.session.connection.state is spotify.ConnectionState.LOGGED_IN)

    def login_listener(self, session):
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            self.logged_in_event.set()

    def get_playlists(self):
        if self.playlists is None:
            self.playlists = self.session.playlist_container.load()
        return len(self.playlists)

    def get_playlist(self):

        playlist = self.playlists.pop()
        if len(self.playlists) == 0:
            self.playlists = None
        return playlist.load()
