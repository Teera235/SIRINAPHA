/**
 * LINE Messaging API Client
 *
 * Provides push message functionality using @line/bot-sdk for
 * delivering daily FSI summaries and alerts to registered fishermen.
 *
 * Requirements: 6.2, 6.5
 */

import { messagingApi, MessageAPIResponseBase } from "@line/bot-sdk";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const LINE_CHANNEL_ACCESS_TOKEN =
  process.env.LINE_CHANNEL_ACCESS_TOKEN ?? "";
const LINE_CHANNEL_SECRET = process.env.LINE_CHANNEL_SECRET ?? "";

/**
 * Create a LINE MessagingApiClient instance.
 * Exported for testing — production code should use the singleton below.
 */
export function createLineClient(): messagingApi.MessagingApiClient {
  if (!LINE_CHANNEL_ACCESS_TOKEN) {
    throw new Error("Missing LINE_CHANNEL_ACCESS_TOKEN environment variable");
  }
  return new messagingApi.MessagingApiClient({
    channelAccessToken: LINE_CHANNEL_ACCESS_TOKEN,
  });
}

/** Lazy singleton */
let _client: messagingApi.MessagingApiClient | null = null;

export function getLineClient(): messagingApi.MessagingApiClient {
  if (!_client) {
    _client = createLineClient();
  }
  return _client;
}

/**
 * Returns the channel secret used for webhook signature verification.
 */
export function getChannelSecret(): string {
  if (!LINE_CHANNEL_SECRET) {
    throw new Error("Missing LINE_CHANNEL_SECRET environment variable");
  }
  return LINE_CHANNEL_SECRET;
}

// ---------------------------------------------------------------------------
// Push message helpers
// ---------------------------------------------------------------------------

export interface PushResult {
  success: boolean;
  error?: string;
}

/**
 * Push a text message to a single LINE user.
 */
export async function pushTextMessage(
  lineUserId: string,
  text: string,
  client?: messagingApi.MessagingApiClient
): Promise<PushResult> {
  const c = client ?? getLineClient();
  try {
    await c.pushMessage({
      to: lineUserId,
      messages: [{ type: "text", text }],
    });
    return { success: true };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Unknown LINE API error";
    return { success: false, error: message };
  }
}

/**
 * Push a daily FSI summary to a fisherman via LINE.
 * The message is pre-formatted in Thai by the FSI Thai text formatter.
 */
export async function pushDailyFSISummary(
  lineUserId: string,
  thaiSummaryText: string,
  client?: messagingApi.MessagingApiClient
): Promise<PushResult> {
  return pushTextMessage(lineUserId, thaiSummaryText, client);
}

/**
 * Push a mangrove alert notification to a Community_Rep via LINE.
 */
export async function pushMangroveAlert(
  lineUserId: string,
  alertText: string,
  client?: messagingApi.MessagingApiClient
): Promise<PushResult> {
  return pushTextMessage(lineUserId, alertText, client);
}

/**
 * Reply to a LINE message (used in webhook handler).
 */
export async function replyTextMessage(
  replyToken: string,
  text: string,
  client?: messagingApi.MessagingApiClient
): Promise<PushResult> {
  const c = client ?? getLineClient();
  try {
    await c.replyMessage({
      replyToken,
      messages: [{ type: "text", text }],
    });
    return { success: true };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Unknown LINE API error";
    return { success: false, error: message };
  }
}

// ---------------------------------------------------------------------------
// Signature verification
// ---------------------------------------------------------------------------

import crypto from "crypto";

/**
 * Verify LINE webhook signature using HMAC-SHA256.
 * Returns true if the signature is valid.
 */
export function verifySignature(
  body: string,
  signature: string,
  channelSecret: string
): boolean {
  const hash = crypto
    .createHmac("SHA256", channelSecret)
    .update(body)
    .digest("base64");
  return hash === signature;
}
