import crypto from 'crypto';

/**
 * Validates merchant postback webhook signature using HMAC-SHA256
 */
export function verifyHmacSignature(rawBody, signatureHeader, secret) {
  if (!signatureHeader || !secret) return false;
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(rawBody);
  const expectedSignature = hmac.digest('hex');
  
  try {
    return crypto.timingSafeEqual(
      Buffer.from(expectedSignature, 'utf-8'),
      Buffer.from(signatureHeader, 'utf-8')
    );
  } catch {
    return false;
  }
}
