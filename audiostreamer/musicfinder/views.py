from django.shortcuts import render_to_response
from musicfinder.smbutils import SMBUtil
from django.http import HttpResponse

from smb.base import NotConnectedError

# Create your views here.

def discover_music(request):
    smb_util = SMBUtil()
    hosts = smb_util.discover_smb_shares()
    counter = 0

    for host in hosts:
        print(host)
        try:
            smb_connection = smb_util.get_smb_connection_with_shares(host)
        except NotConnectedError:
            counter += 1
            continue
        
        for share in smb_connection["shares"]:
            smb_util.find_all_music_files(host, smb_connection["connection"], share)
        smb_connection["connection"].close()

    return HttpResponse(counter)

