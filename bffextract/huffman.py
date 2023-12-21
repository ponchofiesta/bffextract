import typing

from bffextract.util import byte2int, copy_stream, error

def decompress_stream(reader: typing.BinaryIO, writer: typing.BinaryIO, size: int):
    # TODO: implement decompress
    copy_stream(reader, writer, size)
    
    #decompressor = HuffmanDecompressor()
    #decompressor.decompress_stream(reader, writer, size)


class HuffmanDecompressor:
    def __init__(self) -> None:
         self._total_read = 0
         self._treelevels = 0
         self._inodesin = []
         self._symbolsin = []
         self._tree = []
         self._symbol_size = 0
         self._symbol_eob = []

    def decompress_stream(self, reader: typing.BinaryIO, writer: typing.BinaryIO, size: int):
        '''Decompress defined size of reader stream and writer extracted data to writer stream.'''
        self._parse_header(reader)
        self._decode(reader, writer)

    def _parse_header(self, reader: typing.BinaryIO):
        '''Parse compression header of file.'''
        self._total_read = 0
        self._treelevels = byte2int(reader.read(1))
        self._total_read += 1
        self._inodesin = [0] * self._treelevels
        self._symbolsin = [0] * self._treelevels
        self._tree = [0] * self._treelevels
        self._treelevels -= 1
        self._symbol_size = 1

        for i in range(self._treelevels):
            byte = reader.read(1)
            self._symbolsin[i] = byte
            self._symbol_size += byte2int(self._symbolsin[i])

        self._total_read += self._treelevels
        if self._symbol_size > 256:
            error("Bad symbol table")

        #symbol_eob = symbol = [0] * symbol_size
        self._symbol_eob = []
        self._symbolsin[self._treelevels] += 1

        for i in range(self._treelevels):
            # This is wrong!
            self._tree[i] = self._symbol_eob
            for j in range(byte2int(self._symbolsin[i])):
                byte = reader.read(1)
                # This maybe wrong!
                self._symbol_eob.append(byte)
            self._total_read += byte2int(self._symbolsin[i])

        self._symbolsin[self._treelevels] += 1

        self._fill_inodesin(0)

    def _fill_inodesin(self, level: int):
        if level < self._treelevels:
            self._fill_inodesin(level + 1)
            self._inodesin[level] = int(self._inodesin[level + 1] + byte2int(self._symbolsin[level + 1]) / 2)
        else:
            self._inodesin[level] = 0

    def _decode(self, reader: typing.BinaryIO, writer: typing.BinaryIO):
        '''Decode input stream to output stream.'''
        level = 0
        code = 0
        byte = 0
        inlevelindex = 0

        while (byte := reader.read(1)):
            byte = byte2int(byte)
            self._total_read += 1
            for i in range(7, -1, -1):
                code = (code << 1) | ((byte >> i) & 1)
                if code >= self._inodesin[level]:
                    inlevelindex = code - self._inodesin[level]
                    if inlevelindex > byte2int(self._symbolsin[level]):
                        error('Invalid file format: Invalid level index')
                    symbol = self._tree[level][inlevelindex]
                    # This is wrong!!!
                    if symbol == self._symbol_eob:
                        return
                    writer.write(symbol)
                    code = 0
                    level = 0
                else:
                    level += 1
                    if level > self._treelevels:
                        error('Invalid file format: tree level too big.')
