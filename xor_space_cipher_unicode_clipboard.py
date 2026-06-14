#!/usr/bin/env python3
"""
xor_space_cipher_unicode.py

XOR-based text cipher that keeps regular spaces unchanged and supports Arabic
and any other Unicode text by encrypting UTF-8 bytes instead of Python characters.

New enhancement:
- After encrypting or decrypting text from the menu, the result is automatically
  copied to the clipboard when the operating system allows it.

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
import platform
import shutil
import string
import subprocess
import sys
import tempfile

SPACE_BYTE = 0x20
HEX_DIGITS = set(string.hexdigits)


# ---------------------------------------------------------------------------
# Clipboard helpers
# ---------------------------------------------------------------------------
def copy_text_to_clipboard(text: str) -> tuple[bool, str]:
    """
    Try to copy text to the system clipboard.

    Uses only the Python standard library plus common system clipboard commands.

    Supported methods:
    - Windows: native Unicode clipboard API, good for Arabic text.
    - Android Termux: termux-clipboard-set, when Termux:API is installed.
    - macOS: pbcopy.
    - Linux: wl-copy, xclip, or xsel.
    - Fallback: tkinter clipboard, when available.

    Returns:
        (True, message) if copied.
        (False, message) if clipboard access is not available.
    """
    errors: list[str] = []

    if platform.system().lower() == "windows":
        try:
            _copy_windows_unicode(text)
            return True, "copied to clipboard"
        except Exception as exc:
            errors.append(f"Windows clipboard failed: {exc}")

    # Termux / Android command, if installed.
    if shutil.which("termux-clipboard-set"):
        ok, message = _copy_with_command(["termux-clipboard-set"], text)
        if ok:
            return True, "copied to clipboard using termux-clipboard-set"
        errors.append(message)

    # macOS command.
    if shutil.which("pbcopy"):
        ok, message = _copy_with_command(["pbcopy"], text)
        if ok:
            return True, "copied to clipboard using pbcopy"
        errors.append(message)

    # Wayland Linux.
    if shutil.which("wl-copy"):
        ok, message = _copy_with_command(["wl-copy"], text)
        if ok:
            return True, "copied to clipboard using wl-copy"
        errors.append(message)

    # X11 Linux.
    if shutil.which("xclip"):
        ok, message = _copy_with_command(["xclip", "-selection", "clipboard"], text)
        if ok:
            return True, "copied to clipboard using xclip"
        errors.append(message)

    # X11 Linux alternative.
    if shutil.which("xsel"):
        ok, message = _copy_with_command(["xsel", "--clipboard", "--input"], text)
        if ok:
            return True, "copied to clipboard using xsel"
        errors.append(message)

    # Last fallback. This may fail on systems without a graphical display.
    try:
        _copy_with_tkinter(text)
        return True, "copied to clipboard using tkinter"
    except Exception as exc:
        errors.append(f"tkinter clipboard failed: {exc}")

    if errors:
        return False, "clipboard not available (" + "; ".join(errors[-2:]) + ")"
    return False, "clipboard not available"


def _copy_with_command(command: list[str], text: str) -> tuple[bool, str]:
    """Copy text by sending UTF-8 text to a clipboard command's stdin."""
    try:
        subprocess.run(
            command,
            input=text,
            text=True,
            encoding="utf-8",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
            timeout=5,
        )
        return True, "copied"
    except Exception as exc:
        return False, f"{' '.join(command)} failed: {exc}"


def _copy_with_tkinter(text: str) -> None:
    """Copy text using tkinter, if a GUI display is available."""
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    root.destroy()


def _copy_windows_unicode(text: str) -> None:
    """Copy Unicode text to the Windows clipboard using CF_UNICODETEXT."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    GMEM_ZEROINIT = 0x0040

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL

    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL

    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE

    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL

    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p

    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL

    data = (text + "\0").encode("utf-16le")
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data))
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    locked = kernel32.GlobalLock(handle)
    if not locked:
        kernel32.GlobalFree(handle)
        raise ctypes.WinError(ctypes.get_last_error())

    ctypes.memmove(locked, data, len(data))
    kernel32.GlobalUnlock(handle)

    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(handle)
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        if not user32.EmptyClipboard():
            kernel32.GlobalFree(handle)
            raise ctypes.WinError(ctypes.get_last_error())

        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            raise ctypes.WinError(ctypes.get_last_error())

        # After SetClipboardData succeeds, Windows owns the handle.
        handle = None
    finally:
        user32.CloseClipboard()

    if handle:
        kernel32.GlobalFree(handle)


def print_clipboard_status(text: str) -> None:
    """Copy text to clipboard and print a user-friendly status."""
    copied, message = copy_text_to_clipboard(text)
    if copied:
        print("[Copied to clipboard]")
    else:
        print(f"[Could not copy to clipboard: {message}]")


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
    print("    Text encrypt/decrypt output is copied to clipboard when available.")
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
                print_clipboard_status(encrypted)

            elif choice == "2":
                text = input("Enter text to decrypt: ")
                key = input("Enter key: ")
                decrypted = decrypt_text(text, key)
                print("Decrypted text:")
                print(decrypted)
                print_clipboard_status(decrypted)

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
