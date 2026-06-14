#!/usr/bin/env python3
"""
xor_space_cipher_unicode.py

XOR-based text cipher that keeps regular spaces unchanged and supports Arabic
and any other Unicode text by encrypting UTF-8 bytes instead of Python characters.

Important:
- This is a learning/demo cipher, not real security.
- Each non-space UTF-8 byte becomes two hex characters.
- A normal space " " is kept as a normal space.
- Arabic letters are UTF-8 multi-byte characters, so one Arabic letter becomes
  several hex pairs in the encrypted text.

Menu:
  1) Encrypt text
  2) Decrypt text
  3) Encrypt a text file -> text file
  4) Decrypt a text file -> text file
  5) Run self-tests
  6) Quit
"""

from __future__ import annotations

import os
import string
import sys
import tempfile

SPACE_BYTE = 0x20
HEX_DIGITS = set(string.hexdigits)


# ---------------------------------------------------------------------------
# Core cipher
# ---------------------------------------------------------------------------
def _key_to_bytes(key: str) -> bytes:
    """Return the key encoded as UTF-8 bytes."""
    if key == "":
        raise ValueError("key must not be empty")
    return key.encode("utf-8")


def encrypt_text(plain_text: str, key: str) -> str:
    """
    Encrypt Unicode text.

    The text is first encoded as UTF-8 bytes. Every non-space byte is XOR-ed
    with the repeating key bytes and written as two uppercase hex digits.
    A regular space byte 0x20 is copied as a normal space.
    """
    key_bytes = _key_to_bytes(key)
    plain_bytes = plain_text.encode("utf-8")

    result: list[str] = []
    key_index = 0

    for value in plain_bytes:
        if value == SPACE_BYTE:
            result.append(" ")
        else:
            key_byte = key_bytes[key_index % len(key_bytes)]
            result.append(f"{value ^ key_byte:02X}")
            key_index += 1

    return "".join(result)


def decrypt_text(cipher_text: str, key: str) -> str:
    """
    Decrypt text produced by encrypt_text().

    Normal spaces are converted back to space bytes. Every other two characters
    must be a hex byte.
    """
    key_bytes = _key_to_bytes(key)

    output = bytearray()
    key_index = 0
    i = 0

    while i < len(cipher_text):
        ch = cipher_text[i]

        if ch == " ":
            output.append(SPACE_BYTE)
            i += 1
            continue

        if i + 1 >= len(cipher_text):
            raise ValueError(
                "invalid encrypted text: found a single hex digit at the end"
            )

        pair = cipher_text[i : i + 2]
        if pair[0] not in HEX_DIGITS or pair[1] not in HEX_DIGITS:
            raise ValueError(
                f"invalid encrypted text: expected two hex digits at position {i + 1}, got {pair!r}"
            )

        encrypted_byte = int(pair, 16)
        key_byte = key_bytes[key_index % len(key_bytes)]
        output.append(encrypted_byte ^ key_byte)

        key_index += 1
        i += 2

    try:
        return output.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "decryption produced invalid UTF-8. The key may be wrong, or the encrypted text may be damaged."
        ) from exc


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def encrypt_file(input_path: str, output_path: str, key: str) -> None:
    """Read a UTF-8 text file, encrypt it, and write encrypted text."""
    with open(input_path, "r", encoding="utf-8") as f:
        plain_text = f.read()

    encrypted = encrypt_text(plain_text, key)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(encrypted)


def decrypt_file(input_path: str, output_path: str, key: str) -> None:
    """Read an encrypted text file, decrypt it, and write UTF-8 text."""
    with open(input_path, "r", encoding="utf-8") as f:
        cipher_text = f.read()

    plain_text = decrypt_text(cipher_text, key)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(plain_text)


def _ask_existing_file(prompt: str) -> str:
    path = input(prompt).strip().strip('"')
    if not os.path.isfile(path):
        raise FileNotFoundError(f"file not found: {path}")
    return path


def _ask_output_file(prompt: str) -> str:
    path = input(prompt).strip().strip('"')
    if not path:
        raise ValueError("output file path must not be empty")

    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        raise FileNotFoundError(f"output directory does not exist: {parent}")

    return path


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------
def run_self_tests() -> None:
    """Run basic round-trip tests."""
    samples = [
        "Hello World",
        "صباح الخير",
        "السلام عليكم ورحمة الله",
        "Arabic + English 123: صباح الخير",
        "Symbols !@#$%^&*() and emoji 😀",
        "Multiple   spaces are kept",
        "",
    ]

    keys = [
        "ZOO",
        "secret",
        "مفتاح",
    ]

    for sample in samples:
        for key in keys:
            encrypted = encrypt_text(sample, key)
            decrypted = decrypt_text(encrypted, key)
            assert decrypted == sample, (sample, key, encrypted, decrypted)

    # Spaces must remain spaces in the encrypted output.
    assert encrypt_text("A B", "k") == "2A 29"

    # Empty key is not allowed.
    try:
        encrypt_text("test", "")
    except ValueError:
        pass
    else:
        raise AssertionError("empty key should raise ValueError")

    # Bad encrypted text should be rejected.
    try:
        decrypt_text("ABC", "key")
    except ValueError:
        pass
    else:
        raise AssertionError("odd-length encrypted text should raise ValueError")

    try:
        decrypt_text("ZZ", "key")
    except ValueError:
        pass
    else:
        raise AssertionError("non-hex encrypted text should raise ValueError")

    # File round trip.
    with tempfile.TemporaryDirectory() as tmp:
        plain_path = os.path.join(tmp, "plain.txt")
        encrypted_path = os.path.join(tmp, "encrypted.txt")
        decrypted_path = os.path.join(tmp, "decrypted.txt")

        original = "صباح الخير\nHello Oman\nمرحبا بالعالم"
        with open(plain_path, "w", encoding="utf-8") as f:
            f.write(original)

        encrypt_file(plain_path, encrypted_path, "ZOO")
        decrypt_file(encrypted_path, decrypted_path, "ZOO")

        with open(decrypted_path, "r", encoding="utf-8") as f:
            restored = f.read()

        assert restored == original

    print("All tests passed.")


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------
def print_menu() -> None:
    print()
    print("=== XOR Space-Preserving Cipher - Unicode/Arabic Version ===")
    print("  1) Encrypt text")
    print("  2) Decrypt text")
    print("  3) Encrypt a text file -> text file")
    print("  4) Decrypt a text file -> text file")
    print("  5) Run self-tests")
    print("  6) Quit")


def main() -> int:
    # Helpful when output is redirected on Windows.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                text = input("Enter text to encrypt: ")
                key = input("Enter key: ")
                encrypted = encrypt_text(text, key)
                print("Encrypted text:")
                print(encrypted)

            elif choice == "2":
                text = input("Enter text to decrypt: ")
                key = input("Enter key: ")
                decrypted = decrypt_text(text, key)
                print("Decrypted text:")
                print(decrypted)

            elif choice == "3":
                input_path = _ask_existing_file("Input UTF-8 text file: ")
                output_path = _ask_output_file("Output encrypted text file: ")
                key = input("Enter key: ")
                encrypt_file(input_path, output_path, key)
                print(f"Encrypted file written to: {output_path}")

            elif choice == "4":
                input_path = _ask_existing_file("Input encrypted text file: ")
                output_path = _ask_output_file("Output decrypted UTF-8 text file: ")
                key = input("Enter key: ")
                decrypt_file(input_path, output_path, key)
                print(f"Decrypted file written to: {output_path}")

            elif choice == "5":
                run_self_tests()

            elif choice == "6":
                print("Goodbye.")
                return 0

            else:
                print("Please choose 1, 2, 3, 4, 5, or 6.")

        except (ValueError, FileNotFoundError, OSError) as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
