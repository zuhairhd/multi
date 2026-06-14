#!/usr/bin/env python3
"""
xor_space_cipher.py

XOR-based text cipher that keeps space characters unchanged.

Idea
----
Every non-space character is XOR-ed with a repeating key and written out as a
two-digit hex value (so the output is always printable / copy-paste safe). Space
characters (" ") are passed through untouched, and the key position advances ONLY
on non-space characters — spaces never consume a key character.

    Input text:  hello world
    Key:         key
    Encrypted:   03000017 0c1d161501   (hex words, single space preserved)

Example
-------
    plain     = "hello world"
    key       = "key"
    encrypted = xor_encrypt_keep_spaces(plain, key)   # "....... ......"
    decrypted = xor_decrypt_keep_spaces(encrypted, key)
    assert decrypted == plain

    # Multiple spaces are preserved exactly:
    xor_decrypt_keep_spaces(xor_encrypt_keep_spaces("hello  world", "key"), "key")
    # -> "hello  world"   (double space stays double)

Command line
------------
    python xor_space_cipher.py          # interactive menu (text + file modes)
    python xor_space_cipher.py --test   # run the built-in self-tests

⚠️  SECURITY NOTE
----------------
XOR with a repeating key is a TEACHING TOY ONLY. It is trivially breakable and
must NOT be used to protect real or sensitive data. Use a vetted library such as
`cryptography` (AES-GCM / Fernet) for anything that matters.

Assumes text characters are in the byte range (0..255), e.g. ASCII / Latin-1, so
each XOR result fits in two hex digits. That covers ordinary text.
"""

from __future__ import annotations

import sys

SPACE = " "


# ─────────────────────────────────────────────────────────────────────────────
# Core cipher
# ─────────────────────────────────────────────────────────────────────────────
def xor_encrypt_keep_spaces(text: str, key: str) -> str:
    """Encrypt `text` with a repeating `key`, leaving spaces unchanged.

    Each non-space character becomes a two-digit hex value; each space stays a
    literal " ". The key advances only on non-space characters.

    Raises:
        ValueError: if `key` is empty, or a character is outside the byte range.
    """
    if not key:
        raise ValueError("key must not be empty")

    out: list[str] = []
    key_index = 0
    for ch in text:
        if ch == SPACE:
            out.append(SPACE)                      # keep spaces exactly as-is
            continue
        code = ord(ch)
        if code > 0xFF:
            raise ValueError(
                f"character {ch!r} (code {code}) is outside the 0..255 byte "
                "range supported by two-digit hex output"
            )
        k = ord(key[key_index % len(key)])
        out.append(format(code ^ k, "02x"))        # XOR -> two-digit hex
        key_index += 1                             # advance ONLY for non-space
    return "".join(out)


def xor_decrypt_keep_spaces(cipher_text: str, key: str) -> str:
    """Reverse `xor_encrypt_keep_spaces`.

    Spaces are kept as spaces; every other 2-char hex pair is converted back to a
    character by XOR-ing with the repeating key (key advances only on non-space).

    Raises:
        ValueError: if `key` is empty or the cipher text contains invalid /
            incomplete hex.
    """
    if not key:
        raise ValueError("key must not be empty")

    out: list[str] = []
    key_index = 0
    i = 0
    n = len(cipher_text)
    while i < n:
        ch = cipher_text[i]
        if ch == SPACE:
            out.append(SPACE)                      # preserves multiple spaces
            i += 1
            continue
        pair = cipher_text[i:i + 2]
        if len(pair) != 2:
            raise ValueError(
                f"incomplete hex pair {pair!r} at position {i} "
                "(every encrypted character must be exactly two hex digits)"
            )
        try:
            value = int(pair, 16)
        except ValueError:
            raise ValueError(f"invalid hex pair {pair!r} at position {i}") from None
        k = ord(key[key_index % len(key)])
        out.append(chr(value ^ k))
        key_index += 1
        i += 2
    return "".join(out)


# ─────────────────────────────────────────────────────────────────────────────
# Printable-output guarantee
# ─────────────────────────────────────────────────────────────────────────────
def is_printable_cipher_text(cipher_text: str) -> bool:
    """Return True if `cipher_text` contains only printable, copy-paste-safe
    characters: lowercase hex digits (0-9a-f) and the normal space.

    Encrypted output from `xor_encrypt_keep_spaces` always satisfies this, because
    non-space bytes are written as two-digit lowercase hex and spaces are passed
    through verbatim — raw XOR bytes are never emitted.
    """
    allowed = set("0123456789abcdef ")
    return all(ch in allowed for ch in cipher_text)


# ─────────────────────────────────────────────────────────────────────────────
# File helpers (text file in -> text file out)
# ─────────────────────────────────────────────────────────────────────────────
def encrypt_file(in_path: str, out_path: str, key: str) -> None:
    """Read plaintext from `in_path`, write its encryption to `out_path`."""
    with open(in_path, "r", encoding="utf-8") as f:
        text = f.read()
    result = xor_encrypt_keep_spaces(text, key)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)


def decrypt_file(in_path: str, out_path: str, key: str) -> None:
    """Read cipher text from `in_path`, write its decryption to `out_path`.

    A trailing newline (often added by editors) is ignored so it does not break
    hex-pair alignment; meaningful trailing spaces are preserved.
    """
    with open(in_path, "r", encoding="utf-8") as f:
        cipher_text = f.read().rstrip("\n")
    result = xor_decrypt_keep_spaces(cipher_text, key)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)


# ─────────────────────────────────────────────────────────────────────────────
# Command-line menu
# ─────────────────────────────────────────────────────────────────────────────
def _prompt_key() -> str:
    key = input("Enter key: ")
    if not key:
        raise ValueError("key must not be empty")
    return key


def run_menu() -> None:
    """Simple interactive menu for text and file encrypt/decrypt."""
    options = {
        "1": "Encrypt text",
        "2": "Decrypt text",
        "3": "Encrypt a text file -> text file",
        "4": "Decrypt a text file -> text file",
        "5": "Run self-tests",
        "6": "Quit",
    }
    while True:
        print("\n=== XOR Space-Preserving Cipher (learning tool only) ===")
        for k, v in options.items():
            print(f"  {k}) {v}")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                text = input("Enter text to encrypt: ")
                key = _prompt_key()
                print("Encrypted:", xor_encrypt_keep_spaces(text, key))
            elif choice == "2":
                text = input("Enter hex text to decrypt: ")
                key = _prompt_key()
                print("Decrypted:", xor_decrypt_keep_spaces(text, key))
            elif choice == "3":
                in_path = input("Input file path:  ").strip()
                out_path = input("Output file path: ").strip()
                key = _prompt_key()
                encrypt_file(in_path, out_path, key)
                print(f"Encrypted {in_path!r} -> {out_path!r}")
            elif choice == "4":
                in_path = input("Input file path:  ").strip()
                out_path = input("Output file path: ").strip()
                key = _prompt_key()
                decrypt_file(in_path, out_path, key)
                print(f"Decrypted {in_path!r} -> {out_path!r}")
            elif choice == "5":
                _run_tests()
            elif choice == "6":
                print("Bye.")
                return
            else:
                print("Unknown option, please choose 1-6.")
        except (ValueError, OSError) as exc:
            print(f"Error: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Simple self-tests
# ─────────────────────────────────────────────────────────────────────────────
def _run_tests() -> None:
    """A few simple round-trip / behavior / printability tests."""

    key = "key"

    # 0) Printable output + round trip across a range of spacing patterns.
    cases = [
        "hello world",
        "hello  world",
        "  hello world  ",
        "hello     world",
        "ABC xyz 123",
    ]
    for plain in cases:
        cipher = xor_encrypt_keep_spaces(plain, key)
        assert is_printable_cipher_text(cipher), f"non-printable cipher for {plain!r}"
        assert xor_decrypt_keep_spaces(cipher, key) == plain, f"round trip failed for {plain!r}"

    # Invalid cipher text on decryption must raise ValueError.
    for bad in ("zz", "0", "hello!"):
        try:
            xor_decrypt_keep_spaces(bad, key)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid cipher {bad!r} should raise ValueError")

    # 1) Basic round trip.
    plain = "hello world"
    enc = xor_encrypt_keep_spaces(plain, key)
    assert xor_decrypt_keep_spaces(enc, key) == plain, "basic round trip failed"

    # 2) The single space stays a single space in the cipher.
    assert enc.count(" ") == 1, "single space not preserved in cipher"

    # 3) Double space is preserved through encrypt + decrypt.
    dbl = "hello  world"
    enc_dbl = xor_encrypt_keep_spaces(dbl, key)
    assert enc_dbl.count(" ") == 2, "double space not preserved in cipher"
    assert xor_decrypt_keep_spaces(enc_dbl, key) == dbl, "double space round trip failed"

    # 4) Leading / trailing / many spaces preserved exactly.
    spaced = "   a  b   c "
    assert xor_decrypt_keep_spaces(
        xor_encrypt_keep_spaces(spaced, "k"), "k"
    ) == spaced, "leading/trailing/multi spaces not preserved"

    # 5) Spaces never advance the key: an all-space string is unchanged.
    assert xor_encrypt_keep_spaces("     ", "key") == "     ", "spaces consumed key"

    # 6) Empty key is rejected.
    for fn in (xor_encrypt_keep_spaces, xor_decrypt_keep_spaces):
        try:
            fn("abc", "")
        except ValueError:
            pass
        else:
            raise AssertionError(f"{fn.__name__} should reject an empty key")

    # 7) Invalid hex is rejected on decryption.
    try:
        xor_decrypt_keep_spaces("zz", "key")     # 'zz' is not valid hex
    except ValueError:
        pass
    else:
        raise AssertionError("invalid hex should raise ValueError")

    # 8) Incomplete hex pair is rejected.
    try:
        xor_decrypt_keep_spaces("a", "key")      # single hex digit
    except ValueError:
        pass
    else:
        raise AssertionError("incomplete hex pair should raise ValueError")

    print("All tests passed.")
    # Show the worked example from the task.
    print(f"  plain     = {plain!r}")
    print(f"  key       = {key!r}")
    print(f"  encrypted = {enc!r}")
    print(f"  decrypted = {xor_decrypt_keep_spaces(enc, key)!r}")


if __name__ == "__main__":
    # `--test` runs the self-tests; otherwise launch the interactive menu.
    if len(sys.argv) > 1 and sys.argv[1] in ("--test", "-t", "test"):
        _run_tests()
    else:
        try:
            run_menu()
        except (KeyboardInterrupt, EOFError):
            print("\nInterrupted. Bye.")
