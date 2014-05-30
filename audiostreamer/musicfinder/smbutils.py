import tempfile
import mutagenx

from smb.SMBConnection import SMBConnection
from smb.base import NotConnectedError
from nmb.NetBIOS import NetBIOS

from utils.easyid3_patched import EasyID3Patched

# get nmap support
from libnmap.parser import NmapParser
try:
    from libnmap.process import NmapProcess
except ImportError: 
    from utils.nmap_process_windows import NmapProcessWindows as NmapProcess

from django.conf import settings

from .models import Share
from .models import MusicFile

AUDIO_SUFFIXES = ["mp3"]

ID3_DISCOVER_LENGTH = 2000


class NoInterestingHostsFound(Exception):
    pass


class SMBUtil():

    connections = None

    def __init__(self):
        pass

    def discover_smb_shares(self):
        """
            scan the local network for active smb shares
        """
        # do some host discovery

        nm = NmapProcess(settings.LOCAL_NET, options="-sT -p 139 -n")
        net_bios = NetBIOS(broadcast=True)

        if nm.run() == 0:
            # get the scan report
            report = NmapParser.parse(nm.stdout)
            interesting_hosts = []
            # find the hosts that are online and have an open port that indicates smb
            for host in report.hosts:
                if host.status == "up":
                    if len(host.get_open_ports()) != 0:
                        # check whether it is a host we might access with smb
                        hostname = net_bios.queryIPForName(host.address)[0]
                        if hostname is None:
                            continue
                        interesting_hosts.append({
                            "address": host.address,
                            "hostname": hostname})
        else:
            raise NoInterestingHostsFound

        return interesting_hosts

    def _getFractionOfFile(self, connection, share, path, element, max_length=ID3_DISCOVER_LENGTH):

        temp_file = tempfile.TemporaryFile()

        if max_length > element.file_size:
            max_length = element.file_size

        read_result = connection.retrieveFileFromOffset(share.name, path + '\\' + element.filename, temp_file, max_length=max_length)
        if read_result[1] != max_length:
            raise ValueError("Could not read everything we wanted to read file!")

        temp_file.seek(0)
        return (temp_file, max_length)

    def _get_id3_info(self, file_info):

        id3_info = EasyID3Patched(file_info)
        music_file = MusicFile()
        music_file.title = id3_info[u'title']
        music_file.artist = id3_info[u'artist']
        music_file.album = id3_info[u'album']
        tracknumber = id3_info['tracknumber']
        if not isinstance(tracknumber, str):
            music_file.tracknumber = int(id3_info[u'tracknumber'][0])
        else:
            music_file.tracknumber = int(id3_info[u'tracknumber'])
        music_file.discnumber = id3_info[u'discnumber']

        return music_file


    def find_all_music_files(self, host, connection, share, path='\\'):
        """
            Function that discovers all files that are audio files in the given share.
            Interesting information about the audio files will be saved to the database
        """
        path_content = connection.listPath(share.name, path)
        for element in path_content:
            if element.isDirectory:
                if '.' in element.filename or '..' in element.filename:
                    continue
                if path == '\\':
                    new_path = path + element.filename
                else:
                    new_path = path + '\\' + element.filename
                print(new_path)
                self.find_all_music_files(host, connection, share, new_path)
            else:
                try:
                    if element.filename[-3:] in AUDIO_SUFFIXES:
                        file_info = self._getFractionOfFile(connection, share, path, element)
                        music_file = self._get_id3_info(file_info)
                        music_file.name = element.filename
                        music_file.path = r'{}'.format(path)
                        print(path)
                        print(music_file.path)
                        # check whether the current share is already in our database -> if not create a new one
                        if (Share.objects.filter(name=share.name, computer=host["hostname"]).count() == 0):
                            database_share = Share(computer=connection.remote_name, name=share.name, ip_address=host["address"])
                            database_share.save()
                        else:
                            database_share = Share.objects.get(name=share.name, computer=host["hostname"])

                        music_file.share = database_share

                        #check whether music file already exists
                        if MusicFile.objects.filter(title=music_file.title, artist=music_file.artist, album=music_file.album, tracknumber=music_file.tracknumber, discnumber=music_file.discnumber, share=music_file.share).count() != 0:
                            music_file.save()
                except UnicodeEncodeError:
                    pass
                except mutagenx._id3util.ID3NoHeaderError:
                    pass

    def get_smb_connection_with_shares(self, host):
        connection = SMBConnection("RaspBerryPi$", "K3ks3!", "Testtest", host["hostname"], use_ntlm_v2 = True)

        if not connection.connect(host["address"], 139):
            raise NotConnectedError()

        shares = connection.listShares()

        smb_connection = {
            "connection": connection,
            "shares": [],
        }

        for share in shares:
            if share.isSpecial or share.isTemporary:
                continue
            smb_connection["shares"].append(share)

        return smb_connection

if __name__ == "__main__":

    smb = SMBUtil()
    smb.discover_smb_shares()