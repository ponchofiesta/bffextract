import argparse
import os
import struct
import sys
from collections import namedtuple

FILE_MAGIC = 0x09006BEA
HUFFMAN_MAGIC = 0xEA6C
HEADER_MAGICS = [0xEA6B, HUFFMAN_MAGIC, 0xEA6D]

# // FileHeader is at the start of a BFF file.
# //
# // Size: 0x48
# Magic  uint32  // [0x00] =0x09006BEA
# Checksum  uint32  // [0x04]
# CurrentDate uint32  // [0x08]
# StartingDate uint32  // [0x0C]
# Unk10  uint32  // [0x10]
# DiskName  [8]byte // [0x14] "by name\0"
# Unk1C  uint32  // [0x1C]
# Unk20  uint32  // [0x20]
# FilesystemName  [8]byte // [0x24] "by name\0"
# Unk2C  uint32  // [0x2C]
# Unk30  uint32  // [0x30]
# Username  [8]byte // [0x24] "BUILD\0\0\0"
# Unk3C  uint32  // [0x3C]
# Unk40  uint32  // [0x40]
# Unk44  uint32  // [0x44]
FileHeader = namedtuple(
    "FileHeader", "Magic Checksum CurrentDate StartingDate Unk10 DiskName Unk1C Unk20 FilesystemName Unk2C Unk30 Username Unk3C Unk40 Unk44")
FILE_HEADER_PATTERN = '>IIIII8sII8sII8sIII'
FILE_HEADER_SIZE = struct.calcsize(FILE_HEADER_PATTERN)

# // RecordHeader is the first structure of a record.
# // It precedes the record name (variable-length string).
# //
# // Size: 0x40
# Unk00  uint16 // [0x00]
# Magic  uint16 // [0x02] one of MAGICS
# Unk04  uint32 // [0x04]
# Unk08  uint32 // [0x08]
# Unk0C  uint32 // [0x0C]
# UID    uint32 // [0x10]
# GID    uint32 // [0x14]
# Size  uint32 // [0x18] Mask of file size?
# Time1C uint32 // [0x1C]
# Time20 uint32 // [0x20]
# Time24 uint32 // [0x24]
# Unk28  uint32 // [0x28]
# Unk2C  uint32 // [0x2C]
# Unk30  uint32 // [0x30]
# Unk34  uint32 // [0x34]
# CompressedSize   uint32 // [0x38] File size
# Unk3C  uint32 // [0x3C]
RecordHeader = namedtuple(
    "RecordHeader", "Unk00 Magic Unk04 Unk08 Unk0C UID GID Size Time1C Time20 Time24 Unk28 Unk2C Unk30 Unk34 CompressedSize Unk3C ")
RECORD_HEADER_PATTERN = '<HHIIIIIIIIIIIIIII'
RECORD_HEADER_SIZE = struct.calcsize(RECORD_HEADER_PATTERN)

# Unk00 uint32 // [0x00]
# Unk04 uint32 // [0x04]
# Unk08 uint32 // [0x08]
# Unk0C uint32 // [0x0C]
# Unk10 uint32 // [0x10]
# Unk14 uint32 // [0x14]
# Unk18 uint32 // [0x18]
# Unk1C uint32 // [0x1C]
# Unk20 uint32 // [0x20]
# Unk24 uint32 // [0x24]
RecordTrailer = namedtuple(
    "RecordTrailer", "Unk00 Unk04 Unk08 Unk0C Unk10 Unk14 Unk18 Unk1C Unk20 Unk24")
RECORD_TRAILER_PATTERN = '<IIIIIIIIII'
RECORD_TRAILER_SIZE = struct.calcsize(RECORD_TRAILER_PATTERN)


def read_struct(reader, structure, pattern):
    '''Read a struct from reader.'''
    size = struct.calcsize(pattern)
    data = reader.read(size)
    if len(data) == 0:
        return None
    result = structure._make(struct.unpack(pattern, data))
    return result


def read_aligned_string(reader) -> str:
    '''Read string from stream until NULL.'''
    result = b''
    while True:
        data = reader.read(8)
        if len(data) == 0:
            return ''
        for c in data:
            if c == 0:
                return result.decode('utf-8')
            result += c.to_bytes(1, byteorder='big')


def dump_record(reader, name: str, size, uncompress, target_dir):
    '''Read date from stream and write to file.'''
    # TODO: implement uncompress
    if not name:
        return
    out_name = os.path.join(target_dir, name)
    out_name = os.path.normpath(out_name)
    dir = os.path.dirname(out_name)

    if dir != '':
        os.makedirs(dir, exist_ok=True)

    if uncompress:
        warn(f'Unimplemented: {name} is compressed but we cannot uncompress.')

    with open(out_name, "wb") as file:
        total = 0
        to_read = min(1024, size)
        while total < size:
            data = reader.read(to_read)
            file.write(data)
            total += to_read
            to_read = min(1024, size - total)


def parse_args():
    parser = argparse.ArgumentParser(
        prog='BFFextract', description='Extract content of BFF file (AIX Backup file format).')
    parser.add_argument('filename')
    parser.add_argument(
        '-C', '--chdir', help='Extract to this base directory.', default=os.getcwd())
    args = parser.parse_args()
    return args


def eprint(msg):
    print(msg, file=sys.stderr)


def warn(msg):
    eprint(f'WARNING: {msg}')


def error(msg: str):
    eprint(f'ERROR: {msg}')


def die(msg):
    error(msg)
    exit(1)


if __name__ == '__main__':

    args = parse_args()
    target_dir = args.chdir

    with open(args.filename, "rb") as reader:
        file_header = read_struct(reader, FileHeader, FILE_HEADER_PATTERN)
        if file_header.Magic != FILE_MAGIC:
            die('Invalid file format: magic not found.')

        while True:
            record_header = read_struct(
                reader, RecordHeader, RECORD_HEADER_PATTERN)
            if record_header is None:
                break

            filename = read_aligned_string(reader)

            record_trailer = read_struct(
                reader, RecordTrailer, RECORD_TRAILER_PATTERN)
            if record_trailer is None:
                break

            if record_header.Size > 0:
                uncompress = record_header.Magic == HUFFMAN_MAGIC
                dump_record(
                    reader, filename, record_header.CompressedSize, uncompress, target_dir)

            aligned_up = (record_header.CompressedSize + 7) & ~7
            reader.seek(int(aligned_up - record_header.CompressedSize), 1)
