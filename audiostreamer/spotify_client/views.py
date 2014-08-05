from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.conf import settings

from spotify_client.utils import SpotifyHandler

import json

# Create your views here.

def index(request):
    return render_to_response('spotify_index.html')




