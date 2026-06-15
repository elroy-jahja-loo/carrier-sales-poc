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
  average_accepted_rate: number;
  average_accepted_loadboard_rate: number;
  average_accepted_premium_percent: number;
  average_negotiation_rounds: number;
  negotiation_acceptance_rate: number;
  follow_up_count: number;
  sentiment: Record<SentimentKey, number>;
  outcomes: Record<OutcomeKey, number>;
  bookings_over_time: Array<{ date: string; calls: number }>;
};

export type CallRecord = {
  id: number;
  created_at: string;
  happyrobot_run_id: string | null;
  session_id: string | null;
  mc_number: string | null;
  carrier_name: string | null;
  load_id: string | null;
  origin: string | null;
  destination: string | null;
  equipment_type: string | null;
  pickup_datetime: string | null;
  delivery_datetime: string | null;
  loadboard_rate: number | null;
  final_offer: number | null;
  commodity_type: string | null;
  weight: number | null;
  miles: number | null;
  num_of_pieces: number | null;
  dimensions: string | null;
  transfer_successful: boolean | null;
  failure_reason: string | null;
  call_duration_seconds: number | null;
  outcome: OutcomeKey;
  sentiment: SentimentKey;
  call_summary: string | null;
  transcript: string | null;
  negotiation_rounds: number | null;
};

export type CallsResponse = {
  total: number;
  limit: number;
  offset: number;
  calls: CallRecord[];
};
