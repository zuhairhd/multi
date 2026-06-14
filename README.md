# multi

A small collection of standalone projects.

## Contents

- **Catch the Fish Multiplication Game** — `Catch_the_Fish_Multiplication_Game.html`
  (also served as `index.html`). Open the HTML file in a browser to play.
- **XOR Space Cipher** — `xor_space_cipher.py`. A learning tool that encrypts and
  decrypts text with a repeating-key XOR while keeping spaces unchanged.
- **DITTO-style File Dump Utility** — `ditto_file_dump.py`. Dumps any file in
  fixed-length records with CHAR, ZONE, and NUMR lines.

## XOR Space Cipher

The cipher keeps spaces unchanged and outputs encrypted bytes as hexadecimal so the
encrypted text is always printable and copy-paste safe.

- Regular spaces (and multiple / leading / trailing spaces) are preserved exactly.
- The key advances only for non-space characters.
- Every non-space character is emitted as two lowercase hex digits (`0-9a-f`); raw
  XOR bytes are never printed. The output contains only `0-9a-f` and spaces.

The **same file** `xor_space_cipher.py` handles both encryption and decryption — for
text and for files. There is no separate decrypt program.

### Usage

```bash
python xor_space_cipher.py                                          # interactive menu
python xor_space_cipher.py --test                                   # run the self-tests
python xor_space_cipher.py encrypt "hello world" "key"
python xor_space_cipher.py decrypt "030015070a 0e0417150f" "key"
python xor_space_cipher.py encrypt-file original.txt encrypted.txt "key"
python xor_space_cipher.py decrypt-file encrypted.txt decrypted.txt "key"
```

Decrypting an encrypted file reproduces the original text exactly, including single,
multiple, leading, and trailing spaces.

> This XOR cipher is for learning only and is not secure for real sensitive data.

## DITTO-style File Dump Utility

`ditto_file_dump.py` dumps binary or text files in fixed-length records with CHAR, ZONE, and NUMR lines.

Examples:

```bash
python ditto_file_dump.py sample.bin
python ditto_file_dump.py sample.bin --record-length 80
python ditto_file_dump.py sample.bin --encoding cp037 --output dump.txt
python ditto_file_dump.py --test
```

- Default record length is 80.
- Record length can be changed from the CLI (`--record-length` / `-l`).
- ZONE and NUMR are generated from the raw bytes.
- CHAR is display-only using the selected encoding (`ascii`, `latin1`, or `cp037`);
  non-printable or undecodable bytes show as `.`.
