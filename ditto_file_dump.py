#!/usr/bin/env python3
"""
ditto_file_dump.py

Dump any file in a fixed-record format inspired by the IBM DITTO / ESA dump
screens. Each record is shown with a CHAR view, a ZONE line (high hex nibble of
each byte), a NUMR line (low hex nibble of each byte), and a position ruler.

    * * * FILE DUMP * * *
    INPUT FILE: hello.txt
    RECORD LENGTH: 80
    ENCODING: ascii

    BLK     1   DATA    11
             CHAR Hello World
             ZONE 4666674666
             NUMR 85CCF0A7C4
                  01...5...10...11

    FILE HAS 11 BYTES IN 1 BLKS, MIN BLK=11, MAX BLK=11

Key rules
---------
- Default record length is 80; override with --record-length / -l.
- ZONE and NUMR are always built from the RAW bytes (never the decoded text).
- CHAR is display-only, decoded with the selected encoding; any byte that is
  non-printable or cannot be decoded is shown as ".".

Usage
-----
    python ditto_file_dump.py inputfile.bin
    python ditto_file_dump.py inputfile.bin --record-length 120
    python ditto_file_dump.py inputfile.bin --output dump.txt
    python ditto_file_dump.py inputfile.bin --encoding cp037
    python ditto_file_dump.py --test

Standard library only.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

DEFAULT_RECORD_LENGTH = 80

# Encodings supported for the CHAR (display) line. ascii / latin1 are single-byte;
# cp037 is IBM EBCDIC. All are single-byte codecs, so one byte -> one character.
SUPPORTED_ENCODINGS = {"ascii", "latin1", "latin-1", "cp037"}

# Column offsets so CHAR / ZONE / NUMR content and the ruler all line up.
_LABEL_INDENT = " " * 9          # before the CHAR/ZONE/NUMR label
_CONTENT_PAD = " " * 5           # label ("CHAR ") width, used to indent the ruler


# ─────────────────────────────────────────────────────────────────────────────
# Building blocks
# ─────────────────────────────────────────────────────────────────────────────
def make_ruler(length: int) -> str:
    """Return a position ruler up to `length`, e.g. for 80:

        01...5...10...15...20...25...30...35...40...45...50...55...60...65...70...75...80

    Markers fall on 1 and every multiple of 5; if `length` is not a multiple of
    5 its exact value is appended so the ruler always ends at `length`.
    """
    if length <= 0:
        return ""
    parts = ["01"]
    for marker in range(5, length + 1, 5):
        parts.append("..." + str(marker))
    if length % 5 != 0:
        parts.append("..." + str(length))
    return "".join(parts)


def byte_to_display_char(value: int, encoding: str) -> str:
    """Return a single display character for `value`, decoded with `encoding`.

    Non-printable or undecodable bytes render as ".". (Note: a normal space
    decodes to a space and is considered printable, so it is shown as a space.)
    """
    try:
        ch = bytes([value]).decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return "."
    if len(ch) == 1 and ch.isprintable():
        return ch
    return "."


def format_record(record: bytes, block_number: int, record_length: int,
                  encoding: str) -> str:
    """Format one record (BLK header + CHAR / ZONE / NUMR / ruler lines).

    `record_length` is the configured width; the ruler and DATA reflect the
    record's ACTUAL length (which is shorter for a final partial record).
    """
    data_len = len(record)

    char_line = "".join(byte_to_display_char(b, encoding) for b in record)
    hex_pairs = [f"{b:02X}" for b in record]
    zone_line = "".join(p[0] for p in hex_pairs)
    numr_line = "".join(p[1] for p in hex_pairs)
    ruler = make_ruler(data_len)

    lines = [
        f"BLK {block_number:>5}   DATA {data_len:>5}",
        f"{_LABEL_INDENT}CHAR {char_line}",
        f"{_LABEL_INDENT}ZONE {zone_line}",
        f"{_LABEL_INDENT}NUMR {numr_line}",
        f"{_LABEL_INDENT}{_CONTENT_PAD}{ruler}",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Whole-file dump
# ─────────────────────────────────────────────────────────────────────────────
def dump_file(input_path: str, record_length: int = DEFAULT_RECORD_LENGTH,
              encoding: str = "ascii") -> str:
    """Read `input_path` and return its full DITTO-style dump as a string.

    Raises:
        ValueError: record_length not positive, or encoding unsupported.
        FileNotFoundError: input file does not exist.
    """
    if record_length <= 0:
        raise ValueError("record length must be a positive integer")
    if encoding.lower() not in SUPPORTED_ENCODINGS:
        raise ValueError(
            f"unsupported encoding {encoding!r}; "
            f"choose one of: {', '.join(sorted(SUPPORTED_ENCODINGS))}"
        )
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"input file not found: {input_path}")

    with open(input_path, "rb") as f:
        data = f.read()

    header = [
        "* * * FILE DUMP * * *",
        f"INPUT FILE: {input_path}",
        f"RECORD LENGTH: {record_length}",
        f"ENCODING: {encoding}",
    ]

    records = [data[i:i + record_length] for i in range(0, len(data), record_length)]

    blocks = []
    for index, record in enumerate(records, start=1):
        blocks.append(format_record(record, index, record_length, encoding))

    total_bytes = len(data)
    if records:
        lengths = [len(r) for r in records]
        footer = (f"FILE HAS {total_bytes} BYTES IN {len(records)} BLKS, "
                  f"MIN BLK={min(lengths)}, MAX BLK={max(lengths)}")
    else:
        footer = "FILE HAS 0 BYTES IN 0 BLKS"

    sections = ["\n".join(header), ""]
    for block in blocks:
        sections.append(block)
        sections.append("")          # blank line between records
    sections.append(footer)
    return "\n".join(sections) + "\n"


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dump a file in a fixed-record DITTO/ESA-style format.")
    parser.add_argument("input", nargs="?", help="path to the file to dump")
    parser.add_argument("-l", "--record-length", type=int,
                        default=DEFAULT_RECORD_LENGTH,
                        help="bytes per record (default: 80)")
    parser.add_argument("-o", "--output",
                        help="write the dump to this file (default: stdout)")
    parser.add_argument("-e", "--encoding", default="ascii",
                        help="encoding for the CHAR line: ascii, latin1, cp037")
    parser.add_argument("--test", action="store_true",
                        help="run the built-in self-tests")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.test:
        return _run_tests()

    if not args.input:
        parser.error("an input file is required (or use --test)")

    try:
        if args.record_length <= 0:
            raise ValueError("record length must be a positive integer")
        if args.output:
            parent = os.path.dirname(os.path.abspath(args.output))
            if not os.path.isdir(parent):
                raise ValueError(f"output directory does not exist: {parent}")

        dump = dump_file(args.input, args.record_length, args.encoding)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(dump)
            print(f"Dump written to {args.output!r}")
        else:
            sys.stdout.write(dump)
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Self-tests
# ─────────────────────────────────────────────────────────────────────────────
def _run_tests() -> int:
    # 1) ruler at 80 contains 80
    assert "80" in make_ruler(80), "ruler(80) missing 80"
    # 2) ruler at 40 contains 40
    assert "40" in make_ruler(40), "ruler(40) missing 40"
    assert make_ruler(80).startswith("01"), "ruler should start at 01"

    # helper: dump bytes via a temp file
    def dump_bytes(data: bytes, **kw) -> str:
        d = tempfile.mkdtemp(prefix="ditto_test_")
        p = os.path.join(d, "sample.bin")
        try:
            with open(p, "wb") as f:
                f.write(data)
            return dump_file(p, **kw)
        finally:
            os.remove(p)
            os.rmdir(d)

    # 3) ASCII dump for b"Hello World"
    out = dump_bytes(b"Hello World", record_length=80, encoding="ascii")
    assert "CHAR Hello World" in out, "ASCII CHAR view wrong"
    assert "DATA    11" in out, "DATA length wrong for 11 bytes"

    # 4) record splitting with length 5: "HelloWorld" -> 2 blocks
    out = dump_bytes(b"HelloWorld", record_length=5, encoding="ascii")
    assert "BLK     1" in out and "BLK     2" in out, "expected 2 blocks"
    assert "BLK     3" not in out, "should not have a 3rd block"

    # 5) final short record shows actual length
    out = dump_bytes(b"HelloWorld!", record_length=5, encoding="ascii")  # 5,5,1
    assert "BLK     3" in out and "DATA     1" in out, "short final block length wrong"

    # 6) ZONE / NUMR correct for b"Hello"
    rec = format_record(b"Hello", 1, 5, "ascii")
    assert "ZONE 46666" in rec, f"ZONE wrong: {rec!r}"
    assert "NUMR 85CCF" in rec, f"NUMR wrong: {rec!r}"

    # 7) non-printable bytes display as "."
    assert byte_to_display_char(0x00, "ascii") == ".", "NUL should be ."
    assert byte_to_display_char(0x0A, "ascii") == ".", "newline should be ."
    assert byte_to_display_char(0x80, "ascii") == ".", "undecodable ascii byte should be ."
    assert byte_to_display_char(0x41, "ascii") == "A", "0x41 should be A"
    assert byte_to_display_char(0x20, "ascii") == " ", "0x20 should be a space"

    # 8) empty file summary
    out = dump_bytes(b"", record_length=80, encoding="ascii")
    assert "FILE HAS 0 BYTES IN 0 BLKS" in out, "empty file summary wrong"

    # 9) CP037 (EBCDIC) display: 0xC1 -> 'A', 0x40 -> ' '
    assert byte_to_display_char(0xC1, "cp037") == "A", "cp037 0xC1 should be A"
    assert byte_to_display_char(0x40, "cp037") == " ", "cp037 0x40 should be space"
    # ZONE/NUMR stay raw even when decoded with cp037
    rec = format_record(b"\xC1\xC2\xC3", 1, 80, "cp037")   # EBCDIC 'ABC'
    assert "CHAR ABC" in rec, f"cp037 CHAR wrong: {rec!r}"
    assert "ZONE CCC" in rec and "NUMR 123" in rec, f"cp037 ZONE/NUMR wrong: {rec!r}"

    # validation
    try:
        dump_bytes(b"x", record_length=0)
    except ValueError:
        pass
    else:
        raise AssertionError("record_length 0 should raise ValueError")
    try:
        dump_bytes(b"x", encoding="utf-16")
    except ValueError:
        pass
    else:
        raise AssertionError("unsupported encoding should raise ValueError")

    print("All tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
