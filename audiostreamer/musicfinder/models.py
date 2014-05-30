from django.db import models
import ast

class CharListField(models.TextField):
    """
        Class helping to store lists of strings in database
        see: http://justcramer.com/2008/08/08/custom-fields-in-django/
    """
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(CharListField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            value = []
        if isinstance(value, list):
            return value
        
        return ast.literal_eval(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return value

        #assert(isinstance(value, list) or isinstance(value, tuple))

        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

class Share(models.Model):

    computer = models.CharField(max_length=260)
    name = models.CharField(max_length=260)
    ip_address = models.GenericIPAddressField()


class MusicFile(models.Model):

    share = models.ForeignKey(Share)
    path = models.CharField(max_length=260)
    name = models.CharField(max_length=260)
    title = CharListField(blank=True, null=True, default=None)
    artist = CharListField(blank=True, null=True, default=None)
    album = CharListField(blank=True, null=True, default=None)
    tracknumber = models.IntegerField(null=True, default=None)
    discnumber = models.CharField(max_length=260, blank=True, null=True, default=None)
