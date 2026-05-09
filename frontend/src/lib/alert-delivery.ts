/**
 * Mangrove Alert Delivery Pipeline
 *
 * Delivers mangrove alerts to Community_Rep users via LINE and
 * Web Dashboard within 30 minutes of alert detection.
 *
 * Requirements: 6.4
 */

import type { MangroveAlert, UserProfile } from "@/types";
import { pushMangroveAlert, type PushResult } from "./line-client";
import { deliverMessage, logDelivery, type DeliveryRecipient } from "./delivery-service";
import type { messagingApi } from "@line/bot-sdk";
import type { SupabaseClient } from "@supabase/supabase-js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AlertDeliveryResult {
  alert_id: string;
  recipients_notified: number;
  recipients_failed: number;
  delivery_details: Array<{
    user_id: string;
    channel: "line" | "sms" | "web";
    status: "sent" | "failed" | "fallback_sms";
    error?: string;
  }>;
  delivered_within_sla: boolean;
  delivery_time_ms: number;
}

// ---------------------------------------------------------------------------
// Alert text formatting
// ---------------------------------------------------------------------------

/**
 * Format a mangrove alert as Thai text for LINE/SMS delivery.
 */
export function formatAlertText(alert: MangroveAlert): string {
  const levelEmoji = alert.alert_level === "critical" ? "🔴" : "🟡";
  const levelThai =
    alert.alert_level === "critical" ? "วิกฤต" : "เตือนภัย";

  const changeDirection = alert.change_percent > 0 ? "เพิ่มขึ้น" : "ลดลง";
  const absChange = Math.abs(alert.change_percent).toFixed(1);

  return (
    `${levelEmoji} แจ้งเตือนป่าชายเลน — ระดับ${levelThai}\n\n` +
    `📍 พื้นที่: ${alert.area_id}\n` +
    `📉 NDVI ปัจจุบัน: ${alert.ndvi_current.toFixed(3)}\n` +
    `📊 NDVI เฉลี่ย 6 เดือน: ${alert.ndvi_6month_avg.toFixed(3)}\n` +
    `📐 เปลี่ยนแปลง: ${changeDirection} ${absChange}%\n` +
    `🕐 ตรวจพบเมื่อ: ${new Date(alert.detected_at).toLocaleString("th-TH")}\n\n` +
    `กรุณาตรวจสอบพื้นที่และดำเนินการตามความเหมาะสม`
  );
}

// ---------------------------------------------------------------------------
// Alert delivery pipeline
// ---------------------------------------------------------------------------

/** 30-minute SLA in milliseconds */
const SLA_MS = 30 * 60 * 1000;

/**
 * Deliver a mangrove alert to all Community_Rep users responsible
 * for the affected area.
 *
 * Steps:
 * 1. Query Community_Rep users for the alert's area
 * 2. Push alert via LINE to each recipient
 * 3. Mark alert as delivered in web dashboard (via database flag)
 * 4. Verify delivery within 30-minute SLA
 *
 * Requirement 6.4
 */
export async function deliverMangroveAlert(
  alert: MangroveAlert,
  deps: {
    supabase: SupabaseClient;
    lineClient?: messagingApi.MessagingApiClient;
  }
): Promise<AlertDeliveryResult> {
  const startTime = Date.now();
  const alertText = formatAlertText(alert);

  // 1. Find Community_Rep users responsible for this area
  const { data: areaUsers } = await deps.supabase
    .from("user_fishing_areas")
    .select("user_id")
    .eq("area_id", alert.area_id);

  const userIds = (areaUsers ?? []).map(
    (r: { user_id: string }) => r.user_id
  );

  // 2. Fetch user profiles for Community_Rep users
  const { data: users } = await deps.supabase
    .from("users")
    .select("*")
    .in("id", userIds.length > 0 ? userIds : ["__none__"])
    .eq("user_type", "Community_Rep");

  const recipients = (users ?? []) as Array<{
    id: string;
    line_user_id: string | null;
    phone_number: string | null;
    preferred_channel: "line" | "sms";
  }>;

  // 3. Deliver to each recipient
  const deliveryDetails: AlertDeliveryResult["delivery_details"] = [];
  let notified = 0;
  let failed = 0;

  for (const user of recipients) {
    const recipient: DeliveryRecipient = {
      user_id: user.id,
      line_user_id: user.line_user_id,
      phone_number: user.phone_number,
      preferred_channel: user.preferred_channel,
    };

    const result = await deliverMessage(
      {
        recipient,
        message_type: "alert",
        thai_text: alertText,
      },
      {
        lineClient: deps.lineClient,
        supabase: deps.supabase,
      }
    );

    if (result.status === "sent" || result.status === "fallback_sms") {
      notified++;
    } else {
      failed++;
    }

    deliveryDetails.push({
      user_id: user.id,
      channel: result.channel,
      status: result.status as "sent" | "failed" | "fallback_sms",
      error: result.error,
    });
  }

  // 4. Mark alert as web-dashboard visible (insert notification record)
  await deps.supabase.from("delivery_logs").insert({
    user_id: recipients[0]?.id ?? "system",
    channel: "web",
    message_type: "alert",
    status: "sent",
    content_preview: alertText.substring(0, 200),
    sent_at: new Date().toISOString(),
  });

  const deliveryTimeMs = Date.now() - startTime;

  return {
    alert_id: alert.id,
    recipients_notified: notified,
    recipients_failed: failed,
    delivery_details: deliveryDetails,
    delivered_within_sla: deliveryTimeMs <= SLA_MS,
    delivery_time_ms: deliveryTimeMs,
  };
}
