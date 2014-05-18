from django.shortcuts import render_to_response
from smbutils import SMBUtil
from django.http import HttpResponse

# Create your views here.

def discover_music(request):
    smb_util = SMBUtil()
    hosts = smb_util.discover_smb_shares()

    for host in hosts:
        smb_connection = smb_util.get_smb_connection_with_shares(host)
        for share in smb_connection["shares"]:
            smb_util.find_all_music_files(smb_connection["connection"], share)
        smb_connection["connection"].close()

    return HttpResponse(len(hosts))

