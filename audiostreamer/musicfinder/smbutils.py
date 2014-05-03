import tempfile
from smb.SMBConnection import SMBConnection
from mutagenx.easyid3 import EasyID3

from django.conf import settings
from models import Share
from models import MusicFile

AUDIO_SUFFIXES = ["mp3"]

ID3_DISCOVER_LENGTH = 2000


class SMBUtil():

    connections = None

    def __init__(self):
        pass

    def discover_smb_shares():
        """
            scan the local network for active smb shares
        """
        pass

    def getFractionOfFile(self, connection, share, path, element, max_length=ID3_DISCOVER_LENGTH):

        temp_file = tempfile.TemporaryFile()

        if max_length > element.file_size:
            max_length = element.file_size

        read_result = connection.retrieveFileFromOffset(share.name, path + '\\' + element.filename, temp_file, max_length=max_length)
        if read_result[1] != max_length:
            raise ValueError("Could not read everything we wanted to read file!")

        temp_file.seek(0)
        return (temp_file, max_length)

    def get_id3_info(self, file_info):

        id3_info = EasyID3Patched(file_info)
        music_file = MusicFile()
        music_file.title = id3_info['title']
        music_file.artist = id3_info['artist']
        music_file.album = id3_info['album']
        music_file.tracknumber = int(id3_info['tracknumber'])
        music_file.discnumber = id3_info['discnumber']

        return music_file


    def find_all_music_files(self, connection, share, path='\\'):
        """
            Function that discovers all files that are audio files in the given share.
            Interesting information about the audio files will be saved to the database
        """
        path_content = connection["smb_share"].listPath(share.name, path)
        for element in path_content:
            if element.isDirectory:
                if '.' in element.filename or '..' in element.filename:
                    continue
                if path == '\\':
                    new_path = path + element.filename
                else:
                    new_path = path + '\\' + element.filename
                find_all_music_files(connection, share, new_path)
            else:
                try:
                    if element.filename[-3:] in AUDIO_SUFFIXES:
                        file_info = self.getFractionOfFile(connection["smb_share"], share, path, element)
                        music_file = get_id3_info(file_info)
                        music_file.name = element.filename
                        music_file.path = path
                        # check whether the current share is already in our database -> if not create a new one
                        if (Share.objects.filter(name=share.name, computer=connection["computer"]).count() == 0):
                            database_share = Share(computer=connection.remote_name, name=share.name, ip_address=connection["ip_address"])
                            database_share.save()
                        else:
                            database_share = Share.objects.get(name=share.name, computer=connection["computer"])

                        music_file.share = database_share
                        music_file.save()
