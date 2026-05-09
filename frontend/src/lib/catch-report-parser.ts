/**
 * Catch Report Parser
 *
 * Parses incoming text messages from fishermen reporting catch data.
 * Supports Thai language input in the format:
 *   "ผลจับ [species] [weight] [species] [weight] ..."
 *
 * Requirements: 6.7
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CatchSpecies {
  name: string;
  weight_kg: number;
}

export interface ParsedCatchReport {
  species: CatchSpecies[];
  total_kg: number;
  catch_date: string; // YYYY-MM-DD
}

// ---------------------------------------------------------------------------
// Parser
// ---------------------------------------------------------------------------

/** Keywords that trigger catch report parsing */
const CATCH_KEYWORDS = ["ผลจับ", "รายงานผลจับ", "จับได้", "catch"];

/**
 * Parse a text message into a catch report.
 * Returns null if the message is not a catch report.
 *
 * Expected format: "ผลจับ ปลาทู 5 กุ้ง 3"
 * → species: [{name: "ปลาทู", weight_kg: 5}, {name: "กุ้ง", weight_kg: 3}]
 */
export function parseCatchReport(text: string): ParsedCatchReport | null {
  const trimmed = text.trim();
  if (!trimmed) return null;

  // Check if message starts with a catch keyword
  const lowerText = trimmed.toLowerCase();
  const matchedKeyword = CATCH_KEYWORDS.find((kw) =>
    lowerText.startsWith(kw.toLowerCase())
  );
  if (!matchedKeyword) return null;

  // Remove the keyword prefix
  const remainder = trimmed.substring(matchedKeyword.length).trim();
  if (!remainder) return null;

  // Parse species-weight pairs
  // Tokenize by whitespace
  const tokens = remainder.split(/\s+/);
  const species: CatchSpecies[] = [];

  let i = 0;
  while (i < tokens.length) {
    const token = tokens[i];
    // Try to parse as number (weight)
    const num = parseFloat(token);

    if (isNaN(num)) {
      // This is a species name — look ahead for weight
      const speciesName = token;
      if (i + 1 < tokens.length) {
        const nextNum = parseFloat(tokens[i + 1]);
        if (!isNaN(nextNum) && nextNum > 0) {
          species.push({ name: speciesName, weight_kg: nextNum });
          i += 2;
          continue;
        }
      }
      // No weight found — skip this token
      i++;
    } else {
      // Standalone number without species name — skip
      i++;
    }
  }

  if (species.length === 0) return null;

  const total_kg = species.reduce((sum, s) => sum + s.weight_kg, 0);
  const today = new Date();
  const catch_date = today.toISOString().split("T")[0];

  return { species, total_kg, catch_date };
}
