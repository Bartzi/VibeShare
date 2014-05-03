import tempfile
import smb
import mutagenx as mutagen
from smb.SMBConnection import SMBConnection
from mutagenx.easyid3 import EasyID3

AUDIO_SUFFIXES = ["mp3"]

# There will be some mechanism to capture userID, password, client_machine_name, server_name and server_ip
# client_machine_name can be an arbitary ASCII string
# server_name should match the remote machine name, or else the connection will be rejected
conn = SMBConnection("RaspBerryPi$", "K3ks3!", "Testtest", "DATENKRAKE", use_ntlm_v2 = True)
#conn = SMBConnection("guest", "", "Testtest", "DATENKRAKE", use_ntlm_v2 = True)
print(conn.connect("192.168.1.14", 139))

shares = conn.listShares()

def list_content_of_share(connection, share, path='\\'):

	print(path)
	path_contents = connection.listPath(share.name, path)
	for element in path_contents:
		if element.isDirectory:
			if '.' in element.filename or '..' in element.filename:
				continue
			if path == '\\':
				new_path = path + element.filename
			else:
				new_path = path + '\\' + element.filename
			print("listing content of: {}".format(new_path))
			list_content_of_share(connection, share, new_path)
		else:
			try:
				if element.filename[-3:] in AUDIO_SUFFIXES:
					full_path = "\\\\DATENKRAKE\\" + share.name + path + '\\' + element.filename
					audio = EasyID3(full_path)
					print(audio["title"])
					print(audio.pprint())
			except UnicodeEncodeError:
				print("encode Error")
			except mutagen._id3util.ID3NoHeaderError:
				print("no valid id3 header")
root = '\\'

# list all shares
for share in shares:
	print(share.name)
	if share.isSpecial or share.isTemporary: 
		continue
	list_content_of_share(conn, share)

conn.close()