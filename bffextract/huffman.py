import typing

from bffextract.util import error

def decompress_stream(reader: typing.BinaryIO, writer: typing.BinaryIO, size: int):
    decompressor = HuffmanDecompressor()
    decompressor.decompress_stream(reader, writer, size)


class HuffmanDecompressor:
    def __init__(self) -> None:
         self._total_read = 0
         self._treelevels = 0
         self._inodesin = []
         self._symbolsin = []
         self._tree = []
         self._symbol_size = 0
         self._size = 0

    def decompress_stream(self, reader: typing.BinaryIO, writer: typing.BinaryIO, size: int):
        '''Decompress defined size of reader stream and writer extracted data to writer stream.'''
        self._size = size
        self._parse_header(reader)
        self._decode(reader, writer)

    def _parse_header(self, reader: typing.BinaryIO):
        '''Parse compression header of file.'''
        self._treelevels = ord(reader.read(1))
        self._total_read = 1
        self._inodesin = [0] * self._treelevels
        self._symbolsin = [0] * self._treelevels
        self._tree = [[]] * self._treelevels
        self._treelevels -= 1
        self._symbol_size = 1

        for i in range(self._treelevels + 1):
            byte = reader.read(1)
            self._symbolsin[i] = ord(byte)
            self._symbol_size += self._symbolsin[i]

        self._total_read += self._treelevels
        if self._symbol_size > 256:
            error("Bad symbol table")

        self._symbolsin[self._treelevels] += 1

        for i in range(self._treelevels + 1):
            symbol = []
            for j in range(self._symbolsin[i]):
                byte = reader.read(1)
                symbol.append(ord(byte))
            self._tree[i] = symbol
            self._total_read += self._symbolsin[i]

        self._symbolsin[self._treelevels] += 1

        self._fill_inodesin(0)

    def _fill_inodesin(self, level: int):
        if level < self._treelevels:
            self._fill_inodesin(level + 1)
            self._inodesin[level] = int((self._inodesin[level + 1] + self._symbolsin[level + 1]) / 2)
        else:
            self._inodesin[level] = 0

    def _decode(self, reader: typing.BinaryIO, writer: typing.BinaryIO):
        '''Decode input stream to output stream.'''
        level = 0
        code = 0
        byte = 0
        inlevelindex = 0
        treelens = [len(l) for l in self._tree]

        while self._total_read < self._size and (byte := reader.read(1)):
            self._total_read += 1
            byte = ord(byte)

            for i in range(7, -1, -1):
                code = (code << 1) | ((byte >> i) & 1)
                if code >= self._inodesin[level]:
                    inlevelindex = code - self._inodesin[level]
                    if inlevelindex > self._symbolsin[level]:
                        error('Invalid file format: Invalid level index')
                    if treelens[level] <= inlevelindex:
                        # Hopefully the end of the file
                        return
                    symbol = self._tree[level][inlevelindex].to_bytes(1, 'big')
                    writer.write(symbol)
                    code = 0
                    level = 0
                else:
                    level += 1
                    if level > self._treelevels:
                        error('Invalid file format: tree level too big.')
