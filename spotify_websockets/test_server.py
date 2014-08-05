#-*- coding: utf-8 -*-
import asyncio
import spotify
import threading
import configparser
import bson
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

class SpotifyHandler():
    playlists = None

    def __init__(self, session):
        self.websocket = session
        self.session = None
        self.logged_in_event = None
        self.pause = False
        self.delivered_bytes = 0
        self.timeout_timer = threading.Timer(0.5, self.on_timeout)

    def initialise(self):
        print("doing stuff")
        try:
            print(self.session)
        except Exception as e:
            print(e)
        self.logged_in_event = threading.Event()
        if self.session:
            self.websocket.sendMessage(bson.serialize_to_bytes({"message":"created connection to spotify"}), True)
            print("created connection to spotify")
            return
        try:
            print("1")
            self.session = spotify.Session()
            loop = spotify.EventLoop(self.session)
            loop.start()
            print("2")
            self.session.on(spotify.SessionEvent.CONNECTION_STATE_UPDATED, self.login_listener)
            self.session.on(spotify.SessionEvent.MUSIC_DELIVERY, self.music_deliverer)
            self.session.on(spotify.SessionEvent.END_OF_TRACK, self.end_of_track_handler)
            print("3")
            config = configparser.ConfigParser()
            config.read("config")
            spotify_config = config["SPOTIFY"]
            print("4")

            self.session.login(spotify_config["user"], spotify_config["password"])
            print("5")

            print("logging in")
            self.logged_in_event.wait()

            assert(self.session.connection.state is spotify.ConnectionState.LOGGED_IN)

            self.websocket.sendMessage(bson.serialize_to_bytes({"message": "created connection to spotify"}), True)
            print("sent")
        except Exception as e:
            print(e)
            print(self.session)
        print("created connection to spotify")



    def login_listener(self, session):
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            self.logged_in_event.set()


    def music_deliverer(self, session, audio_format, frames, num_frames):
        if self.pause:
            print("streaming paused")
            return 0
        print(len(frames))

        if self.delivered_bytes > 204800:
            # time for a 2 second break
            print("taking a break")
            self.pause = True
            self.timeout_timer.start()
            return 0

        #data = bson.serialize_to_bytes({"message": "musicdata", "audioData": frames})
        print("generated data")
        self.websocket.sendMessage(frames, True)
        self.delivered_bytes += num_frames
        return num_frames

    def end_of_track_handler(self, session):
      print("track ended")
      session.player.unload()

    def playlists(self):
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
        try:
            playlist = playlist.load()
            #self.wamp_session.publish("com.vibeshare.metainformation", json.dumps(playlist, cls=PlaylistEnocder))
        except Exception as e:
            print(e)

    def play(self):
        try:
          #spotify:track:6EuArluBSbxlFs4vtQ3cYR
            track = self.session.get_track("spotify:track:27y5jZCsr3sy4lfno0QMfM").load(timeout=30)
            self.session.player.load(track)
            self.session.player.play()
            self.loop = 0
        except Exception as e:
            print(e)

    def pause_loading(self):
        self.pause = True

    def resume_loading(self):
        self.pause = False

    def stop_playing(self):
        self.session.player.unload()

    def on_timeout(self):
        print("resuming streaming")
        self.timeout_timer = threading.Timer(2.0, self.on_timeout)
        self.delivered_bytes = 0
        self.pause = False



class MyServerProtocol(WebSocketServerProtocol):


   def send_message(self, message):
      i = 0
      while i < 50:
         print("bla")
         self.sendMessage(bytes("{} {}".format(message, i), 'utf-8'), False)
         i += 1

   def onConnect(self, request):
      print("Client connecting: {0}".format(request.peer))
      try:
        self.spotify_session = SpotifyHandler(self)
        self.spotify_session.initialise()
        self.spotify_session.stop_playing()
      except Exception as e:
        print("Exception: {}".format(e))
        

   def onOpen(self):

      print("WebSocket connection open.")

   def onMessage(self, payload, isBinary):
      if isBinary:
         print("Binary message received: {0} bytes".format(len(payload)))
         print(payload)
         message = bson.parse_bytes(payload)
         print(message)
         if message['message'] == 'play':
                self.spotify_session.play()
                return
         if message['message'] == 'pause':
                print("pausing")
                self.spotify_session.pause_loading()
                return
         if message['message'] == 'resume':
                self.spotify_session.resume_loading()
                return
         if message['message'] == 'playlist':
                self.spotify_session.playlists()

         bla = bson.serialize_to_bytes(message)
         self.sendMessage(bla, isBinary)
         print(bla)
      else:
         print(payload)
         message = bson.parse_bytes(payload)
         print(message)
         self.sendMessage(bson.serialize_to_bytes(message), isBinary)

      ## echo back message verbatim
      self.sendMessage(payload, isBinary)

   def onClose(self, wasClean, code, reason):
      print("WebSocket connection closed: {0}".format(reason))



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