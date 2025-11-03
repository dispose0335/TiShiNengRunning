"""
AES Encryption/Decryption Utility Module

This module provides AES encryption and decryption functionality with support for
both CBC and ECB modes. It handles proper padding for different data types including
strings with multi-byte characters (UTF-8, GBK).

Example:
    from AesUtils import AESCrypto

    # Initialize with key and IV for CBC mode
    aes = AESCrypto(key='your-16-byte-key', iv='your-16-byte-iv')

    # Encrypt text
    encrypted = aes.encrypt('Hello World')

    # Decrypt text
    decrypted = aes.decrypt(encrypted)
"""

import os
from typing import Union, Optional

from Crypto.Cipher import AES
from base64 import b64decode, b64encode

# AES block size constant
BLOCK_SIZE = AES.block_size

# PKCS7 padding function for strings
# Note: Handles multi-byte characters (UTF-8: 3 bytes, GBK: 2 bytes per character)
# Uses len(s.encode()) instead of len(s) for proper byte length calculation
pad = lambda s: s + (BLOCK_SIZE - len(s.encode()) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s.encode()) % BLOCK_SIZE)

# Remove PKCS7 padding
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

# Zero padding function for strings
zero_pad = lambda s: s + (BLOCK_SIZE - len(s.encode()) % BLOCK_SIZE) * chr(0)


def bytes_pad(data: bytes) -> bytes:
    """
    Apply PKCS7 padding to bytes data.

    Args:
        data (bytes): Raw bytes data to be padded

    Returns:
        bytes: Padded bytes data ready for AES encryption
    """
    pad_length = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + bytes([pad_length] * pad_length)


class AESCrypto:
    def __init__(self, key: Union[str, bytes], iv: Union[str, bytes], ecb_mode: bool = False):
        """
        Initialize AES encryption/decryption utility.

        Args:
            key (Union[str, bytes]): Encryption key (must be 16, 24, or 32 bytes)
            iv (Union[str, bytes]): Initialization vector (must be 16 bytes, ignored in ECB mode)
            ecb_mode (bool): If True, use ECB mode; if False, use CBC mode (default: False)

        Note:
            ECB mode is less secure and should only be used for compatibility.
            CBC mode is recommended for better security.
        """
        if isinstance(key, str):
            key = key.encode()
        if isinstance(iv, str):
            iv = iv.encode()

        self.key = key
        self.iv = iv
        self.ecb_mode = ecb_mode

    def encrypt(self, text: Union[str, bytes], zero_padding: bool = False, is_bytes: bool = False) -> str:
        """
        Encrypt data using AES encryption.

        Process: Apply padding -> AES encryption -> Base64 encoding

        Args:
            text (Union[str, bytes]): Plaintext to encrypt
            zero_padding (bool): If True, use zero padding; if False, use PKCS7 padding
            is_bytes (bool): If True, treat input as bytes; if False, treat as string

        Returns:
            str: Base64 encoded encrypted data

        Example:
            encrypted = aes.encrypt('Hello World')
            encrypted_bytes = aes.encrypt(b'Hello World', is_bytes=True)
        """
        if is_bytes:
            padded_data = bytes_pad(text)
        else:
            if zero_padding:
                padded_data = zero_pad(text).encode()
            else:
                padded_data = pad(text).encode()

        if self.ecb_mode:
            cipher = AES.new(key=self.key, mode=AES.MODE_ECB)
        else:
            cipher = AES.new(key=self.key, mode=AES.MODE_CBC, IV=self.iv)

        encrypted_data = cipher.encrypt(padded_data)
        return b64encode(encrypted_data).decode('utf-8')

    def decrypt(self, encrypted_text: str, return_bytes: bool = False) -> Union[str, bytes]:
        """
        Decrypt AES encrypted data.

        Process: Base64 decoding -> AES decryption -> Remove padding

        Args:
            encrypted_text (str): Base64 encoded encrypted data
            return_bytes (bool): If True, return bytes; if False, return decoded string

        Returns:
            Union[str, bytes]: Decrypted data as string or bytes

        Example:
            decrypted = aes.decrypt(encrypted_text)
            decrypted_bytes = aes.decrypt(encrypted_text, return_bytes=True)
        """
        encrypted_data = b64decode(encrypted_text)

        if self.ecb_mode:
            cipher = AES.new(key=self.key, mode=AES.MODE_ECB)
        else:
            cipher = AES.new(key=self.key, mode=AES.MODE_CBC, IV=self.iv)

        decrypted_data = cipher.decrypt(encrypted_data)

        if return_bytes:
            return unpad(decrypted_data)
        else:
            return unpad(decrypted_data).decode('utf-8')
