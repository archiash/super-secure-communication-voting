/**
 * Session ID generator.
 * Format: QS-XXXXXXXXX (matching the Figma design, e.g., QS-EJPCF84N)
 */
export function generateSessionId(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let id = 'QS-';
  for (let i = 0; i < 8; i++) {
    id += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return id;
}
