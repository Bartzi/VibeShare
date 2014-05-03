from mutagenx.easyid3 import EasyID3
from id3_patched import ID3Patched

class EasyID3Patched(EasyID3):

	def __init__(self, filename=None):
		self.__id3 = ID3Patched()
        if filename is not None:
            self.load(filename)