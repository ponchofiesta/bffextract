# BFFextract

Simple Python script to extract AIX BFF files.

## Usage

```
usage: BFFextract [-h] [-C CHDIR] filename

Extract content of BFF file (AIX Backup file format).

positional arguments:
  filename

options:
  -h, --help            show this help message and exit
  -C CHDIR, --chdir CHDIR
                        Extract to this base directory.
```

## Limitations

- Decompression is unimplemented. Compressed files are extracted as is.
- Empty folders are not extracted. Currently only files are extracted and their parent folders are created implicitly.
