from django.db import models


class Share(models.Model):

	computer = models.CharField(max_length=260)
	name = models.CharField(max_length=260)
	ip_address = models.GenericIPAddressField()


class MusicFile(models.Model):

	share = models.ForeignKey(Share)
	path = models.CharField(max_length=260)
	name = models.CharField(max_length=260)
	title = models.CharField(max_length=260, blank=True, null=True, default=None)
	artist = models.CharField(max_length=260, blank=True, null=True, default=None)
	album = models.CharField(max_length=260, blank=True, null=True, default=None)
	tracknumber = models.IntegerField(null=True, default=None)
	discnumber = models.IntegerField(null=True, default=None)
