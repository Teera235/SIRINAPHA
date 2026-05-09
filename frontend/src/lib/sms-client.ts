/**
 * SMS Client (Twilio / ThaiBulkSMS)
 *
 * Provides SMS sending functionality as a fallback delivery channel
 * when LINE messaging fails.
 *
 * Requirements: 6.3, 6.8
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const TWILIO_ACCOUNT_SID = process.env.TWILIO_ACCOUNT_SID ?? "";
const TWILIO_AUTH_TOKEN = process.env.TWILIO_AUTH_TOKEN ?? "";
const TWILIO_FROM_NUMBER = process.env.TWILIO_FROM_NUMBER ?? "";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SmsResult {
  success: boolean;
  sid?: string;
  error?: string;
}

// ---------------------------------------------------------------------------
// SMS sending
// ---------------------------------------------------------------------------

/**
 * Send an SMS message via Twilio REST API.
 *
 * Uses fetch() to call the Twilio Messages API directly,
 * avoiding the need for the full twilio npm package.
 */
export async function sendSms(
  to: string,
  body: string
): Promise<SmsResult> {
  if (!TWILIO_ACCOUNT_SID || !TWILIO_AUTH_TOKEN || !TWILIO_FROM_NUMBER) {
    return {
      success: false,
      error: "Twilio credentials not configured (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER)",
    };
  }

  // Truncate SMS body to 1600 chars (Twilio limit for concatenated SMS)
  const truncatedBody = body.length > 1600 ? body.substring(0, 1597) + "..." : body;

  try {
    const url = `https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json`;
    const auth = Buffer.from(
      `${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}`
    ).toString("base64");

    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Basic ${auth}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        To: to,
        From: TWILIO_FROM_NUMBER,
        Body: truncatedBody,
      }).toString(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage =
        (errorData as Record<string, string>).message ??
        `Twilio API error: ${response.status}`;
      return { success: false, error: errorMessage };
    }

    const data = (await response.json()) as { sid?: string };
    return { success: true, sid: data.sid };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Unknown SMS sending error";
    return { success: false, error: message };
  }
}

/**
 * Format a message for SMS delivery.
 * SMS messages are shorter, so we strip emojis and condense the text.
 */
export function formatForSms(thaiText: string): string {
  // Keep the text as-is for Thai SMS — modern networks handle Unicode well
  // Just ensure it's within reasonable length
  if (thaiText.length <= 1600) return thaiText;
  return thaiText.substring(0, 1597) + "...";
}
