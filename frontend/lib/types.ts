export type OutcomeKey =
  | "booked"
  | "declined"
  | "ineligible"
  | "transferred"
  | "no_load_found"
  | "unresolved"
  | "unknown";

export type SentimentKey = "positive" | "neutral" | "negative" | "unknown";

export type MetricsSummary = {
  total_calls: number;
  verified_carriers: number;
  ineligible_carriers: number;
  booked_calls: number;
  declined_calls: number;
  no_load_found_calls: number;
  unresolved_calls: number;
  booking_rate: number;
  average_final_offer: number;
  average_loadboard_rate: number;
  average_premium_percent: number;
  sentiment: Record<SentimentKey, number>;
  outcomes: Record<OutcomeKey, number>;
  bookings_over_time: Array<{ date: string; calls: number }>;
};

export type CallRecord = {
  id: number;
  created_at: string;
  mc_number: string | null;
  carrier_name: string | null;
  load_id: string | null;
  origin: string | null;
  destination: string | null;
  final_offer: number | null;
  outcome: OutcomeKey;
  sentiment: SentimentKey;
  call_summary: string | null;
};

export type CallsResponse = {
  total: number;
  limit: number;
  offset: number;
  calls: CallRecord[];
};
