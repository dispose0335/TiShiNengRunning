"""
RSA Encryption Utility Module

This module provides RSA encryption functionality with support for handling
long messages by chunking them into smaller blocks. It automatically formats
PEM public keys and handles Base64 encoding of encrypted data.

Example:
    from RsaUtils import RSACrypto

    # Initialize with PEM public key (without headers)
    rsa_crypto = RSACrypto('MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMI...')

    # Encrypt string message
    encrypted = rsa_crypto.encrypt('Hello World')

    # Encrypt bytes data
    encrypted_bytes = rsa_crypto.encrypt_bytes(b'Hello World')
"""

import rsa
import base64
from typing import Union


class RSACrypto:
    def __init__(self, public_key: Union[str, bytes]):
        """
        Initialize RSA encryption utility.

        Args:
            public_key (Union[str, bytes]): PEM format public key without headers
                                          (without '-----BEGIN PUBLIC KEY-----' and '-----END PUBLIC KEY-----')

        Example:
            rsa_crypto = RSACrypto('MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMI...')
        """
        self.public_key: bytes = self._format_public_key(public_key)

    @staticmethod
    def _format_public_key(key: Union[str, bytes]) -> bytes:
        """
        Format a public key to proper PEM format.

        Converts a raw public key string to proper PEM format with headers
        and proper line breaks (64 characters per line).

        Args:
            key (Union[str, bytes]): Raw PEM format public key without headers

        Returns:
            bytes: Properly formatted PEM public key with headers and line breaks

        Example:
            Input: 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMI...'
            Output: b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMI...\n-----END PUBLIC KEY-----'
        """
        if isinstance(key, bytes):
            key = key.decode()

        header = '-----BEGIN PUBLIC KEY-----\n'
        footer = '-----END PUBLIC KEY-----'
        formatted_key = ''

        # Split key into 64-character lines
        chunk_size = 64
        num_chunks = len(key) // chunk_size
        num_lines = num_chunks if len(key) % chunk_size == 0 else num_chunks + 1

        for i in range(num_lines):
            start_pos = i * chunk_size
            end_pos = (i + 1) * chunk_size
            formatted_key += key[start_pos:end_pos] + '\n'

        result = header + formatted_key + footer
        return result.encode()

    def encrypt_bytes(self, data: bytes) -> str:
        """
        Encrypt bytes data using RSA encryption.

        This method handles data that fits within RSA block size limits.
        For larger data, use the encrypt() method which handles chunking.

        Args:
            data (bytes): Raw bytes data to encrypt (must be <= 117 bytes for 1024-bit key)

        Returns:
            str: Base64 encoded encrypted data

        Raises:
            OverflowError: If data is too large for RSA block size
                          (e.g., "458 bytes needed for message, but there is only space for 117")

        Example:
            encrypted = rsa_crypto.encrypt_bytes(b'Hello World')
        """
        public_key = rsa.PublicKey.load_pkcs1_openssl_pem(self.public_key)
        encrypted_data = base64.b64encode(rsa.encrypt(data, public_key))
        return encrypted_data.decode()

    def encrypt(self, message: str) -> str:
        """
        Encrypt a string message using RSA encryption with automatic chunking.

        This method handles long messages by splitting them into chunks that fit
        within RSA block size limits (117 bytes for 1024-bit key). Each chunk is
        encrypted separately and concatenated.

        Args:
            message (str): String message to encrypt

        Returns:
            str: Base64 encoded concatenated encrypted chunks

        Note:
            This method automatically handles messages longer than the RSA block size
            by chunking them into 117-byte segments (suitable for 1024-bit RSA keys).

        Example:
            encrypted = rsa_crypto.encrypt('This is a long message that exceeds RSA block size...')
        """
        public_key = rsa.PublicKey.load_pkcs1_openssl_pem(self.public_key)
        encrypted_chunks = b''

        # RSA block size limit for 1024-bit key (128 bytes - 11 bytes padding = 117 bytes)
        max_chunk_size = 117
        num_chunks = len(message) // max_chunk_size
        total_chunks = num_chunks if len(message) % max_chunk_size == 0 else num_chunks + 1

        for i in range(total_chunks):
            start_pos = i * max_chunk_size
            end_pos = (i + 1) * max_chunk_size
            chunk = message[start_pos:end_pos].encode()
            encrypted_chunks += rsa.encrypt(chunk, public_key)

        return base64.b64encode(encrypted_chunks).decode()
