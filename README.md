# multi

A small collection of standalone projects.

## Contents

- **Catch the Fish Multiplication Game** — `Catch_the_Fish_Multiplication_Game.html`
  (also served as `index.html`). Open the HTML file in a browser to play.
- **XOR Space Cipher** — `xor_space_cipher.py`. A learning tool that encrypts and
  decrypts text with a repeating-key XOR while keeping spaces unchanged.
- **XOR Unicode/Arabic Space Cipher** — `xor_space_cipher_unicode.py`. A Unicode-safe
  version of the XOR space cipher that supports Arabic text by encrypting UTF-8
  bytes while keeping regular spaces unchanged.
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

## XOR Unicode/Arabic Space Cipher

`xor_space_cipher_unicode.py` is a Unicode-safe version of the XOR space cipher. It
supports Arabic text and other Unicode text by converting the text to UTF-8 bytes
before applying XOR.

This avoids the `0..255` character limit problem that happens when encrypting Arabic
letters directly as Python characters.

- Regular spaces are preserved exactly.
- The key advances only for non-space UTF-8 bytes.
- Every non-space UTF-8 byte is emitted as two uppercase hex digits (`0-9A-F`).
- Arabic letters usually become multiple hex pairs because UTF-8 stores Arabic
  characters as multiple bytes.
- The same file handles encryption and decryption for text and files.

### Usage

Run the interactive menu:

```bash
python xor_space_cipher_unicode.py
```

On Windows, you can also run:

```bat
py xor_space_cipher_unicode.py
```

Menu options:

```text
1) Encrypt text
2) Decrypt text
3) Encrypt a text file -> text file
4) Decrypt a text file -> text file
5) Run self-tests
6) Quit
```

Example Arabic encryption:

```text
Enter text to encrypt: صباح الخير
Enter key: ZOO
Encrypted text:
82FA97F297E882E2 97FD96CB82E196D097FE
```

Decrypting the encrypted text with the same key returns:

```text
صباح الخير
```

Run self-tests from the menu by choosing option `5`.

If Arabic text does not display correctly in Windows Command Prompt, switch the
console to UTF-8 first:

```bat
chcp 65001
py xor_space_cipher_unicode.py
```

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
