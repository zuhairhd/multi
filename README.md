# multi

A small collection of standalone projects.

## Contents

- **Catch the Fish Multiplication Game** — `Catch_the_Fish_Multiplication_Game.html`
  (also served as `index.html`). Open the HTML file in a browser to play.
- **XOR Space Cipher** — `xor_space_cipher.py`. A learning tool that encrypts and
  decrypts text with a repeating-key XOR while keeping spaces unchanged.

## XOR Space Cipher

The cipher keeps spaces unchanged and outputs encrypted bytes as hexadecimal so the
encrypted text is always printable and copy-paste safe.

- Regular spaces (and multiple / leading / trailing spaces) are preserved exactly.
- The key advances only for non-space characters.
- Every non-space character is emitted as two lowercase hex digits (`0-9a-f`); raw
  XOR bytes are never printed. The output contains only `0-9a-f` and spaces.

### Usage

```bash
python xor_space_cipher.py        # interactive menu (encrypt/decrypt text or files)
python xor_space_cipher.py --test # run the built-in self-tests
```

> This XOR cipher is for learning only and is not secure for real sensitive data.
