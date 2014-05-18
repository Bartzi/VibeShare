from django.contrib import admin
from musicfinder.models import *

# Register your models here.

class ShareAdmin(admin.ModelAdmin):
    pass

class MusicFileAdmin(admin.ModelAdmin):
    pass

admin.site.register(Share, ShareAdmin)
admin.site.register(MusicFile, MusicFileAdmin)
