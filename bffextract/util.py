import sys
import typing


def eprint(msg: str):
    print(msg, file=sys.stderr)


def warn(msg: str):
    eprint(f'WARNING: {msg}')


def error(msg: str):
    eprint(f'ERROR: {msg}')


def die(msg: str):
    error(msg)
    exit(1)


def copy_stream(reader: typing.BinaryIO, writer: typing.BinaryIO, size: int):
    '''Read defined size of reader stream and copy to writer stream.'''
    total = 0
    to_read = min(1024, size)
    while total < size:
        data = reader.read(to_read)
        writer.write(data)
        total += to_read
        to_read = min(1024, size - total)
