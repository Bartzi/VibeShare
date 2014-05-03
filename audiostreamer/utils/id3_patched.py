import struct

from mutagenx._compat import reraise

from mutagenx.id3 import ID3
from mutagenx.id3 import ParseID3v1

from mutagenx._id3util import *
from mutagenx._id3frames import *
from mutagenx._id3specs import *

class ID3Patched(ID3):

    __flags = 0
    __readbytes = 0
    __crc = None
    __unknown_version = None

    _V24 = (2, 4, 0)
    _V23 = (2, 3, 0)
    _V22 = (2, 2, 0)
    _V11 = (1, 1)

    def __fullread(self, size):
        """ Read a certain number of bytes from the source file. """
        try:
            if size < 0:
                raise ValueError('Requested bytes (%s) less than zero' % size)
            if size > self.__filesize:
                size = self.__filesize
        except AttributeError:
            pass
        data = self.__fileobj.read(size)
        self.__readbytes += size
        return data

    def load(self, file, known_frames=None, translate=True, v2_version=4):
        """Load tags from a filename.

        Keyword arguments:

        * filename -- filename to load tag data from
        * known_frames -- dict mapping frame IDs to Frame objects
        * translate -- Update all tags to ID3v2.3/4 internally. If you
                       intend to save, this must be true or you have to
                       call update_to_v23() / update_to_v24() manually.
        * v2_version -- if update_to_v23 or update_to_v24 get called (3 or 4)

        Example of loading a custom frame::

            my_frames = dict(mutagenx.id3.Frames)
            class XMYF(Frame): ...
            my_frames["XMYF"] = XMYF
            mutagenx.id3.ID3(filename, known_frames=my_frames)
        """

        if not v2_version in (3, 4):
            raise ValueError("Only 3 and 4 possible for v2_version")

        from os.path import getsize
        filename = file[0]
        self.filename = filename
        self.__known_frames = known_frames
        self.__fileobj = filename
        #self.__filesize = getsize(filename)
        self.__filesize = file[1]
        try:
            try:
                self.__load_header()
            except (ID3NoHeaderError, ID3UnsupportedVersionError) as err:
                self.size = 0
                import sys
                stack = sys.exc_info()[2]
                try:
                    self.__fileobj.seek(-128, 2)
                except EnvironmentError:
                    reraise(err, None, stack)
                else:
                    frames = ParseID3v1(self.__fileobj.read(128))
                    if frames is not None:
                        self.version = self._V11
                        for v in frames.values():
                            self.add(v)
                    else:
                        reraise(err, None, stack)
            else:
                frames = self.__known_frames
                if frames is None:
                    if self._V23 <= self.version:
                        frames = Frames
                    elif self._V22 <= self.version:
                        frames = Frames_2_2
                data = self.__fullread(self.size - 10)
                for frame in self.__read_frames(data, frames=frames):
                    if isinstance(frame, Frame):
                        self.add(frame)
                    else:
                        self.unknown_frames.append(frame)
                self.__unknown_version = self.version
        finally:
            self.__fileobj.close()
            del self.__fileobj
            del self.__filesize
            if translate:
                if v2_version == 3:
                    self.update_to_v23()
                else:
                    self.update_to_v24()

    def __load_header(self):
        fn = self.filename
        data = self.__fullread(10)
        id3, vmaj, vrev, flags, size = unpack('>3sBBB4s', data)
        self.__flags = flags
        self.size = BitPaddedInt(size) + 10
        self.version = (2, vmaj, vrev)

        if id3 != b'ID3':
            raise ID3NoHeaderError("%r doesn't start with an ID3 tag" % fn)
        if vmaj not in [2, 3, 4]:
            raise ID3UnsupportedVersionError("%r ID3v2.%d not supported"
                                             % (fn, vmaj))

        if self.PEDANTIC:
            if not BitPaddedInt.has_valid_padding(size):
                raise ValueError("Header size not synchsafe")

            if (self._V24 <= self.version) and (flags & 0x0f):
                raise ValueError("%r has invalid flags %#02x" % (fn, flags))
            elif (self._V23 <= self.version < self._V24) and (flags & 0x1f):
                raise ValueError("%r has invalid flags %#02x" % (fn, flags))

        if self.f_extended:
            extsize = self.__fullread(4)
            if extsize.decode('ascii') in Frames:
                # Some tagger sets the extended header flag but
                # doesn't write an extended header; in this case, the
                # ID3 data follows immediately. Since no extended
                # header is going to be long enough to actually match
                # a frame, and if it's *not* a frame we're going to be
                # completely lost anyway, this seems to be the most
                # correct check.
                # http://code.google.com/p/quodlibet/issues/detail?id=126
                self.__flags ^= 0x40
                self.__extsize = 0
                self.__fileobj.seek(-4, 1)
                self.__readbytes -= 4
            elif self.version >= self._V24:
                # "Where the 'Extended header size' is the size of the whole
                # extended header, stored as a 32 bit synchsafe integer."
                self.__extsize = BitPaddedInt(extsize) - 4
                if self.PEDANTIC:
                    if not BitPaddedInt.has_valid_padding(extsize):
                        raise ValueError("Extended header size not synchsafe")
            else:
                # "Where the 'Extended header size', currently 6 or 10 bytes,
                # excludes itself."
                self.__extsize = unpack('>L', extsize)[0]
            if self.__extsize:
                self.__extdata = self.__fullread(self.__extsize)
            else:
                self.__extdata = b''

    def __determine_bpi(self, data, frames, EMPTY=b'\x00' * 10):
        if self.version < self._V24:
            return int
        # have to special case whether to use bitpaddedints here
        # spec says to use them, but iTunes has it wrong

        # count number of tags found as BitPaddedInt and how far past
        o = 0
        asbpi = 0
        while o < len(data) - 10:
            part = data[o:o + 10]
            if part == EMPTY:
                bpioff = -((len(data) - o) % 10)
                break
            name, size, flags = unpack('>4sLH', part)
            size = BitPaddedInt(size)
            o += 10 + size
            if name in frames:
                asbpi += 1
        else:
            bpioff = o - len(data)

        # count number of tags found as int and how far past
        o = 0
        asint = 0
        while o < len(data) - 10:
            part = data[o:o + 10]
            if part == EMPTY:
                intoff = -((len(data) - o) % 10)
                break
            name, size, flags = unpack('>4sLH', part)
            o += 10 + size
            if name in frames:
                asint += 1
        else:
            intoff = o - len(data)

        # if more tags as int, or equal and bpi is past and int is not
        if asint > asbpi or (asint == asbpi and (bpioff >= 1 and intoff <= 1)):
            return int
        return BitPaddedInt

    def __read_frames(self, data, frames):
        if self.version < self._V24 and self.f_unsynch:
            try:
                data = unsynch.decode(data)
            except ValueError:
                pass

        if self._V23 <= self.version:
            bpi = self.__determine_bpi(data, frames)
            while data:
                header = data[:10]
                try:
                    name, size, flags = unpack('>4sLH', header)
                except struct.error:
                    return  # not enough header
                if name.strip(b'\x00') == b'':
                    return

                name = name.decode('latin1')

                size = bpi(size)
                framedata = data[10:10+size]
                data = data[10+size:]
                if size == 0:
                    continue  # drop empty frames
                try:
                    tag = frames[name]
                except KeyError:
                    if is_valid_frame_id(name):
                        yield header + framedata
                else:
                    try:
                        yield self.__load_framedata(tag, flags, framedata)
                    except NotImplementedError:
                        yield header + framedata
                    except ID3JunkFrameError:
                        pass

        elif self._V22 <= self.version:
            while data:
                header = data[0:6]
                try:
                    name, size = unpack('>3s3s', header)
                except struct.error:
                    return  # not enough header
                size, = struct.unpack('>L', b'\x00'+size)
                if name.strip(b'\x00') == b'':
                    return

                name = name.decode('latin1')

                framedata = data[6:6+size]
                data = data[6+size:]
                if size == 0:
                    continue  # drop empty frames
                try:
                    tag = frames[name]
                except KeyError:
                    if is_valid_frame_id(name):
                        yield header + framedata
                else:
                    try:
                        yield self.__load_framedata(tag, 0, framedata)
                    except NotImplementedError:
                        yield header + framedata
                    except ID3JunkFrameError:
                        pass

    def __load_framedata(self, tag, flags, framedata):
        return tag.fromData(self, flags, framedata)

    f_unsynch = property(lambda s: bool(s.__flags & 0x80))
    f_extended = property(lambda s: bool(s.__flags & 0x40))
    f_experimental = property(lambda s: bool(s.__flags & 0x20))
    f_footer = property(lambda s: bool(s.__flags & 0x10))

    def __save_frame(self, frame, name=None, version=_V24, v23_sep=None):
        flags = 0
        if self.PEDANTIC and isinstance(frame, TextFrame):
            if len(str(frame)) == 0:
                return b''

        if version == self._V23:
            framev23 = frame._get_v23_frame(sep=v23_sep)
            framedata = framev23._writeData()
        else:
            framedata = frame._writeData()

        usize = len(framedata)
        if usize > 2048:
            # Disabled as this causes iTunes and other programs
            # to fail to find these frames, which usually includes
            # e.g. APIC.
            #framedata = BitPaddedInt.to_str(usize) + framedata.encode('zlib')
            #flags |= Frame.FLAG24_COMPRESS | Frame.FLAG24_DATALEN
            pass

        if version == self._V24:
            bits = 7
        elif version == self._V23:
            bits = 8
        else:
            raise ValueError

        datasize = BitPaddedInt.to_str(len(framedata), width=4, bits=bits)
        n = (name or type(frame).__name__).encode("ascii")
        header = pack('>4s4sH', n, datasize, flags)
        return header + framedata

    def __update_common(self):
        """Updates done by both v23 and v24 update"""

        if "TCON" in self:
            # Get rid of "(xx)Foobr" format.
            self["TCON"].genres = self["TCON"].genres

        if self.version < self._V23:
            # ID3v2.2 PIC frames are slightly different.
            pics = self.getall("APIC")
            mimes = {"PNG": "image/png", "JPG": "image/jpeg"}
            self.delall("APIC")
            for pic in pics:
                newpic = APIC(
                    encoding=pic.encoding, mime=mimes.get(pic.mime, pic.mime),
                    type=pic.type, desc=pic.desc, data=pic.data)
                self.add(newpic)

            # ID3v2.2 LNK frames are just way too different to upgrade.
            self.delall("LINK")