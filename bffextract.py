'''
bffextract extracts the contents of AIX BFF files.

Based on:
https://github.com/terorie/aix-bff-go
https://github.com/ReFirmLabs/binwalk/blob/cddfede795971045d99422bd7a9676c8803ec5ee/src/binwalk/magic/archives#L226
https://github.com/jtreml/firmware-mod-kit/blob/master/src/bff
'''

import argparse
import os
import typing

from bffextract import bff
from bffextract.util import die, warn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='BFFextract', description='Extract content of BFF file (AIX Backup file format).')
    parser.add_argument('filename', help='Path to BFF file.')
    parser.add_argument('-C', '--chdir', help='Extract to directory.', default=os.getcwd())
    args = parser.parse_args()
    return args


def extract_file(reader: typing.BinaryIO, out_dir: str | os.PathLike):
    '''Extract single file from stream to target directory.'''
    record_header = bff.read_struct(reader, bff.RecordHeader, bff.RECORD_HEADER_PATTERN)
    if record_header is None:
        return False

    filename = bff.read_aligned_string(reader)

    record_trailer = bff.read_struct(reader, bff.RecordTrailer, bff.RECORD_TRAILER_PATTERN)
    if record_trailer is None:
        return False

    if record_header.Size > 0:
        decompress = record_header.Magic == bff.HUFFMAN_MAGIC
        bff.extract_record(reader, filename, record_header.CompressedSize, decompress, out_dir)
    else:
        # TODO: Extract empty folder
        warn(f"Unimplemented: '{filename}' has zero size and will not be extracted.")

    aligned_up = (record_header.CompressedSize + 7) & ~7
    reader.seek(int(aligned_up - record_header.CompressedSize), 1)

    return True
 

if __name__ == '__main__':

    args = parse_args()

    with open(args.filename, "rb") as reader:
        file_header = bff.read_struct(reader, bff.FileHeader, bff.FILE_HEADER_PATTERN)
        if file_header.Magic != bff.FILE_MAGIC:
            die('Invalid file format: magic not found.')

        while extract_file(reader, args.chdir): pass
