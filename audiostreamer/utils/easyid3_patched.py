from mutagenx.easyid3 import EasyID3
from .id3_patched import ID3Patched

from mutagenx._compat import text_type, PY2
from mutagenx._util import dict_match

class EasyID3Patched(EasyID3):

    def __init__(self, filename=None):
        self.__id3 = ID3Patched()
        if filename is not None:
            self.load(filename)

    load = property(lambda s: s.__id3.load,
                    lambda s, v: setattr(s.__id3, 'load', v))

    save = property(lambda s: s.__id3.save,
                    lambda s, v: setattr(s.__id3, 'save', v))

    delete = property(lambda s: s.__id3.delete,
                      lambda s, v: setattr(s.__id3, 'delete', v))

    filename = property(lambda s: s.__id3.filename,
                        lambda s, fn: setattr(s.__id3, 'filename', fn))

    size = property(lambda s: s.__id3.size,
                    lambda s, fn: setattr(s.__id3, 'size', s))

    def __getitem__(self, key):
        key = key.lower()
        func = dict_match(self.Get, key, self.GetFallback)
        if func is not None:
            return func(self.__id3, key)
        else:
            raise EasyID3KeyError("%r is not a valid key" % key)

    def __setitem__(self, key, value):
        key = key.lower()
        if PY2:
            if isinstance(value, basestring):
                value = [value]
        else:
            if isinstance(value, text_type):
                value = [value]
        func = dict_match(self.Set, key, self.SetFallback)
        if func is not None:
            return func(self.__id3, key, value)
        else:
            raise EasyID3KeyError("%r is not a valid key" % key)

    def __delitem__(self, key):
        key = key.lower()
        func = dict_match(self.Delete, key, self.DeleteFallback)
        if func is not None:
            return func(self.__id3, key)
        else:
            raise EasyID3KeyError("%r is not a valid key" % key)

    def __iter__(self):
        keys = []
        for key in self.Get.keys():
            if key in self.List:
                keys.extend(self.List[key](self.__id3, key))
            elif key in self:
                keys.append(key)
        if self.ListFallback is not None:
            keys.extend(self.ListFallback(self.__id3, ""))
        return iter(keys)

    def __len__(self):
        keys = []
        for key in self.Get.keys():
            if key in self.List:
                keys.extend(self.List[key](self.__id3, key))
            elif key in self:
                keys.append(key)
        if self.ListFallback is not None:
            keys.extend(self.ListFallback(self.__id3, ""))
        return len(keys)