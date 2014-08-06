#-*- coding: utf-8 -*-
import asyncio
import spotify
import threading
import configparser
import json
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

class SpotifyHandler:
    """
        Singleton implementation so that different users can use the websocket streaming"
    """

    instance = None
    def __init__(self, peer):
        if not SpotifyHandler.instance:
            SpotifyHandler.instance = SpotifyHandler.__SpotifyHandler(peer)
        else:
            self.instance.peers.append(peer)

    def __getattr__(self, name):
        return getattr(self.instance, name)


    class __SpotifyHandler:
        playlists = None

        def __init__(self, peer):
            self.peers = [peer]
            self.session = None
            self.logged_in_event = None
            self.pause = False
            self.delivered_frames = 0
            self.timeout_timer = threading.Timer(1.0, self.on_timeout)
            self.is_initialised = False
            self.is_playing = False

        def initialise(self):
            print("initialising spotify")
            self.logged_in_event = threading.Event()
            if self.session:
                self.send_to_peers(json.dumps({"message":"created connection to spotify"}).encode('utf-8'), False)
                print("created connection to spotify")
                return
            try:
                self.session = spotify.Session()
                loop = spotify.EventLoop(self.session)
                loop.start()
                config = configparser.ConfigParser()
                config.read("config")
                spotify_config = config["SPOTIFY"]

                self.session.login(spotify_config["user"], spotify_config["password"])
                self.initialise_event_listeners()
                self.logged_in_event.wait()

                assert(self.session.connection.state is spotify.ConnectionState.LOGGED_IN)

                self.send_to_peers(json.dumps({"message": "created connection to spotify"}).encode('utf-8'), False)
                self.is_initialised = True
                print("initialisation complete")
            except Exception as e:
                print(e)
                print(self.session)
            print("created connection to spotify")

        def initialise_event_listeners(self):
            self.session.on(spotify.SessionEvent.CONNECTION_STATE_UPDATED, self.login_listener)
            self.session.on(spotify.SessionEvent.MUSIC_DELIVERY, self.music_delivery_handler)
            self.session.on(spotify.SessionEvent.END_OF_TRACK, self.end_of_track_handler)

        def send_to_peers(self, message, isBinary):
            for peer in self.peers:
                peer.sendMessage(message, isBinary)

        def remove_peer(self, peer):
            self.peers.remove(peer)
            print("removed a peer")

        def login_listener(self, session):
            if session.connection.state is spotify.ConnectionState.LOGGED_IN:
                self.logged_in_event.set()


        def music_delivery_handler(self, session, audio_format, frames, num_frames):
            if self.pause:
                return 0
            if self.delivered_frames > 204800:
                # time for a 2 second break
                self.pause = True
                self.timeout_timer.start()
                return 0

            self.send_to_peers(frames, True)
            self.delivered_frames += num_frames
            return num_frames

        def end_of_track_handler(self, session):
          print("track ended")
          session.player.unload()
          self.is_playing = False

        def get_playlists(self):
                try:
                    print("getting playlists")
                except Exception as e:
                    print(e)
                try:
                    self.playlists = self.session.playlist_container.load()
                    #print("sending data")
                    #self.wamp_session.publish("com.vibeshare.playlistdata", len(self.playlists))
                except Exception as e:
                    print(e)
                for playlist in self.playlists:
                    self.get_playlist(playlist)
                

        def get_playlist(self, playlist):
                playlist = playlist.load()

        def play(self, song_uri):
            #spotify:track:6EuArluBSbxlFs4vtQ3cYR --> utlra song
            print("going to play a new song")
            track = self.session.get_track(song_uri).load(timeout=30)
            self.session.player.load(track)
            self.session.player.play()
            self.delivered_frames = 0
            self.loop = 0
            self.is_playing = True

        def stop_playing(self):
            self.session.player.unload()

        def on_timeout(self):
            self.send_to_peers(json.dumps({"message": "play"}).encode('utf-8'), False)
            self.timeout_timer = threading.Timer(2.0, self.on_timeout)
            self.delivered_frames = 0
            self.pause = False



class MyServerProtocol(WebSocketServerProtocol):


    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        try:
            self.spotify_session = SpotifyHandler(self)
            if not self.spotify_session.is_initialised:
                self.spotify_session.initialise()
        except Exception as e:
            print("Exception: {}".format(e))
        

    def onOpen(self):
        print("WebSocket connection open.")
        if self.spotify_session.is_playing:
            # in order to prevent that the new client is "faster" than the old
            # we need to prevent that he plays the first chunks he gets
            data = {
                "message": "skip",
                "frames": 1,
            }
            print("letting client skip some frames")
            self.sendMessage(json.dumps(data).encode('utf-8'), False)

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print(payload.decode("utf-8"))
            message = json.loads(payload.decode("utf-8"))
            if message['message'] == 'play':
                print("got play message")
                if not self.spotify_session.is_playing:
                    self.spotify_session.play(message["song"])
                return
            if message['message'] == 'playlist':
                self.spotify_session.get_playlists()
            print(payload)
            print(message)

        ## echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        self.spotify_session.remove_peer(self)



if __name__ == '__main__':

    factory = WebSocketServerFactory("ws://0.0.0.0:8080", debug=False)
    factory.protocol = MyServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', 8080)
    server = loop.run_until_complete(coro)

    try:
        print("starting server")
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()