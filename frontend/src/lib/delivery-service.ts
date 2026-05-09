/**
 * Delivery Service
 *
 * Orchestrates message delivery across LINE, SMS, and Web channels.
 * Implements automatic SMS fallback when LINE delivery fails.
 * Logs all delivery attempts to the delivery_logs table.
 *
 * Requirements: 6.2, 6.3, 6.4, 6.5, 6.8
 */

import type {
  DeliveryChannel,
  DeliveryStatus,
  MessageType,
} from "@/types";
import { pushTextMessage, type PushResult } from "./line-client";
import { sendSms, type SmsResult } from "./sms-client";
import type { messagingApi } from "@line/bot-sdk";
import type { SupabaseClient } from "@supabase/supabase-js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DeliveryRecipient {
  user_id: string;
  line_user_id?: string | null;
  phone_number?: string | null;
  preferred_channel: "line" | "sms";
}

export interface DeliveryRequest {
  recipient: DeliveryRecipient;
  message_type: MessageType;
  thai_text: string;
}

export interface DeliveryResult {
  channel: DeliveryChannel;
  status: DeliveryStatus;
  error?: string;
}

// ---------------------------------------------------------------------------
// Core delivery logic
// ---------------------------------------------------------------------------

/**
 * Deliver a message to a recipient, with automatic SMS fallback.
 *
 * Flow:
 * 1. If preferred_channel is "line" and line_user_id exists → try LINE
 * 2. If LINE fails or preferred_channel is "sms" → send via SMS
 * 3. Log delivery attempt to delivery_logs table
 *
 * Requirements: 6.2, 6.3, 6.8
 */
export async function deliverMessage(
  request: DeliveryRequest,
  deps?: {
    lineClient?: messagingApi.MessagingApiClient;
    smsSender?: typeof sendSms;
    supabase?: SupabaseClient;
  }
): Promise<DeliveryResult> {
  const { recipient, message_type, thai_text } = request;
  const smsSender = deps?.smsSender ?? sendSms;

  let result: DeliveryResult;

  // Try LINE first if preferred and available
  if (
    recipient.preferred_channel === "line" &&
    recipient.line_user_id
  ) {
    const lineResult = await pushTextMessage(
      recipient.line_user_id,
      thai_text,
      deps?.lineClient
    );

    if (lineResult.success) {
      result = { channel: "line", status: "sent" };
    } else {
      // LINE failed — fallback to SMS (Requirement 6.8)
      if (recipient.phone_number) {
        const smsResult = await smsSender(recipient.phone_number, thai_text);
        if (smsResult.success) {
          result = { channel: "sms", status: "fallback_sms" };
        } else {
          result = {
            channel: "sms",
            status: "failed",
            error: smsResult.error ?? "SMS delivery failed after LINE fallback",
          };
        }
      } else {
        result = {
          channel: "line",
          status: "failed",
          error: `LINE failed (${lineResult.error}), no phone number for SMS fallback`,
        };
      }
    }
  } else if (recipient.phone_number) {
    // Direct SMS delivery
    const smsResult = await smsSender(recipient.phone_number, thai_text);
    if (smsResult.success) {
      result = { channel: "sms", status: "sent" };
    } else {
      result = {
        channel: "sms",
        status: "failed",
        error: smsResult.error ?? "SMS delivery failed",
      };
    }
  } else {
    result = {
      channel: "line",
      status: "failed",
      error: "No delivery channel available (no line_user_id or phone_number)",
    };
  }

  // Log delivery attempt
  if (deps?.supabase) {
    await logDelivery(deps.supabase, {
      user_id: recipient.user_id,
      channel: result.channel,
      message_type,
      status: result.status,
      content_preview: thai_text.substring(0, 200),
    });
  }

  return result;
}

// ---------------------------------------------------------------------------
// Delivery logging
// ---------------------------------------------------------------------------

interface DeliveryLogEntry {
  user_id: string;
  channel: DeliveryChannel;
  message_type: MessageType;
  status: DeliveryStatus;
  content_preview: string;
}

/**
 * Insert a delivery log entry into the delivery_logs table.
 */
export async function logDelivery(
  supabase: SupabaseClient,
  entry: DeliveryLogEntry
): Promise<void> {
  await supabase.from("delivery_logs").insert({
    user_id: entry.user_id,
    channel: entry.channel,
    message_type: entry.message_type,
    status: entry.status,
    content_preview: entry.content_preview,
    sent_at: new Date().toISOString(),
  });
}
