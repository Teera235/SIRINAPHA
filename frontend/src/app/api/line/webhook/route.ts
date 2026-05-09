/**
 * LINE Webhook Handler
 *
 * Receives webhook events from LINE Messaging API, verifies the
 * signature, and processes incoming messages from fishermen.
 *
 * Supported events:
 * - Text messages containing catch reports → forwarded to Yield Predictor
 * - Follow events → welcome message
 *
 * Requirements: 6.2, 6.5, 6.7
 */

import { NextRequest, NextResponse } from "next/server";
import { getChannelSecret, replyTextMessage, verifySignature } from "@/lib/line-client";
import { parseCatchReport, type ParsedCatchReport } from "@/lib/catch-report-parser";

// ---------------------------------------------------------------------------
// Types for LINE webhook events
// ---------------------------------------------------------------------------

interface LINEWebhookBody {
  events: LINEEvent[];
  destination?: string;
}

interface LINEEvent {
  type: "message" | "follow" | "unfollow" | "postback";
  replyToken: string;
  source: {
    userId: string;
    type: "user" | "group" | "room";
  };
  timestamp: number;
  message?: {
    id: string;
    type: "text" | "image" | "video" | "audio" | "sticker";
    text?: string;
  };
}

// ---------------------------------------------------------------------------
// Signature verification
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------

/**
 * Handle a text message event from a fisherman.
 * Attempts to parse catch report data and replies with confirmation.
 *
 * Requirement 6.7
 */
async function handleTextMessage(
  event: LINEEvent
): Promise<{ type: "catch_report"; data: ParsedCatchReport } | { type: "unknown" }> {
  const text = event.message?.text ?? "";

  // Try to parse as catch report
  const parsed = parseCatchReport(text);
  if (parsed) {
    // Reply with confirmation in Thai
    await replyTextMessage(
      event.replyToken,
      `✅ รับข้อมูลผลจับเรียบร้อยแล้ว\n` +
        `📅 วันที่: ${parsed.catch_date}\n` +
        `🐟 ชนิด: ${parsed.species.map((s) => `${s.name} ${s.weight_kg} กก.`).join(", ")}\n` +
        `📊 รวม: ${parsed.total_kg} กก.\n` +
        `ขอบคุณที่รายงานข้อมูลครับ 🙏`
    );
    return { type: "catch_report", data: parsed };
  }

  // Unknown message — reply with help text
  await replyTextMessage(
    event.replyToken,
    `🐟 สวัสดีครับ! ระบบ Baan-Pla Link\n\n` +
      `📝 รายงานผลจับ:\n` +
      `พิมพ์: "ผลจับ [ชนิดสัตว์น้ำ] [น้ำหนัก กก.]"\n` +
      `ตัวอย่าง: "ผลจับ ปลาทู 5 กุ้ง 3"\n\n` +
      `หากต้องการความช่วยเหลือ พิมพ์ "ช่วยเหลือ"`
  );
  return { type: "unknown" };
}

/**
 * Handle a follow event (new user adds the bot).
 */
async function handleFollowEvent(event: LINEEvent): Promise<void> {
  await replyTextMessage(
    event.replyToken,
    `🎉 ยินดีต้อนรับสู่ Baan-Pla Link!\n\n` +
      `ระบบจะส่งข้อมูลดัชนีความเหมาะสมในการทำประมง (FSI) ให้ท่านทุกวัน\n\n` +
      `📝 ท่านสามารถรายงานผลจับได้โดยพิมพ์:\n` +
      `"ผลจับ [ชนิดสัตว์น้ำ] [น้ำหนัก กก.]"\n` +
      `ตัวอย่าง: "ผลจับ ปลาทู 5 กุ้ง 3"\n\n` +
      `ขอบคุณที่ร่วมเป็นส่วนหนึ่งของชุมชน 🙏`
  );
}

// ---------------------------------------------------------------------------
// POST handler
// ---------------------------------------------------------------------------

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const rawBody = await request.text();

    // Verify LINE signature
    const signature = request.headers.get("x-line-signature") ?? "";
    let channelSecret: string;
    try {
      channelSecret = getChannelSecret();
    } catch {
      return NextResponse.json(
        { error: "LINE channel secret not configured" },
        { status: 500 }
      );
    }

    if (!verifySignature(rawBody, signature, channelSecret)) {
      return NextResponse.json(
        { error: "Invalid signature" },
        { status: 401 }
      );
    }

    // Parse body
    let body: LINEWebhookBody;
    try {
      body = JSON.parse(rawBody) as LINEWebhookBody;
    } catch {
      return NextResponse.json(
        { error: "Invalid JSON body" },
        { status: 400 }
      );
    }

    // Process events
    const results: Array<{ eventType: string; userId: string; result: string }> = [];

    for (const event of body.events) {
      const userId = event.source?.userId ?? "unknown";

      switch (event.type) {
        case "message":
          if (event.message?.type === "text") {
            const msgResult = await handleTextMessage(event);
            results.push({
              eventType: "message",
              userId,
              result: msgResult.type,
            });
          }
          break;

        case "follow":
          await handleFollowEvent(event);
          results.push({
            eventType: "follow",
            userId,
            result: "welcome_sent",
          });
          break;

        case "unfollow":
          results.push({
            eventType: "unfollow",
            userId,
            result: "noted",
          });
          break;

        default:
          results.push({
            eventType: event.type,
            userId,
            result: "ignored",
          });
      }
    }

    return NextResponse.json({ ok: true, processed: results.length });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Internal server error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
