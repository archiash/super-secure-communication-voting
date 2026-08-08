/**
 * OTP (One-Time Pad) encryption/decryption utilities.
 * Encryption and decryption are the same operation: XOR.
 */

/**
 * XOR two bit strings of equal length.
 * @param plaintext - Binary string, e.g. "10110010"
 * @param key - Binary string of same length
 * @returns XOR result as binary string
 */
export function xorEncrypt(plaintext: string, key: string): string {
  if (plaintext.length !== key.length) {
    throw new Error(
      `OTP key length (${key.length}) must match plaintext length (${plaintext.length})`
    );
  }
  return plaintext
    .split('')
    .map((bit, i) => (parseInt(bit) ^ parseInt(key[i])).toString())
    .join('');
}

/** Alias — OTP decryption is the same XOR operation */
export const xorDecrypt = xorEncrypt;

/**
 * Convert a string to its binary representation.
 * Each character becomes 8 bits.
 */
export function textToBinary(text: string): string {
  return text
    .split('')
    .map((char) => char.charCodeAt(0).toString(2).padStart(8, '0'))
    .join('');
}

/**
 * Convert a binary string back to text.
 * Assumes each character is 8 bits.
 */
export function binaryToText(binary: string): string {
  const chars: string[] = [];
  for (let i = 0; i < binary.length; i += 8) {
    const byte = binary.slice(i, i + 8);
    chars.push(String.fromCharCode(parseInt(byte, 2)));
  }
  return chars.join('');
}
