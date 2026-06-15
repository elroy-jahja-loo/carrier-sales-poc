import { CallsResponse, MetricsSummary } from "./types";

const serverBaseUrl = process.env.SERVER_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const serverApiKey = process.env.SERVER_APP_API_KEY || "change-me-local-api-key";

async function fetchBackend<T>(path: string): Promise<T> {
  const response = await fetch(`${serverBaseUrl}${path}`, {
    headers: {
      "X-API-Key": serverApiKey,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Backend request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getSummary(): Promise<MetricsSummary> {
  return fetchBackend<MetricsSummary>("/api/metrics/summary");
}

export async function getCalls(limit = 25): Promise<CallsResponse> {
  return fetchBackend<CallsResponse>(`/api/metrics/calls?limit=${limit}&offset=0`);
}
