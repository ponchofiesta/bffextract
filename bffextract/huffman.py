import typing

from bffextract.util import copy_stream


def decompress_stream(reader: typing.BinaryIO, writer: typing.BinaryIO, size: int):
    '''Decompress defined size of reader stream and writer extracted data to writer stream.'''
    # TODO: implement decompress
    copy_stream(reader, writer, size)