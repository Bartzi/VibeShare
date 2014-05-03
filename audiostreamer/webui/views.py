from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse

from musicfinder.models import Share, MusicFile


def index(request):
    shares = Share.objects.all()
    return render_to_response("webui_index.html", dict(shares=shares), context_instance=RequestContext(request))