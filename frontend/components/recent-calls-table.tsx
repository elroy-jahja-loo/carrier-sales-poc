import { CallRecord } from "@/lib/types";
import { StatusPill } from "./status-pill";

function currency(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "-";
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export function RecentCallsTable({ calls }: { calls: CallRecord[] }) {
  return (
    <div className="glass overflow-hidden rounded-2xl shadow-soft">
      <div className="border-b border-slate-700/60 px-4 py-3">
        <h3 className="font-display text-lg">Recent Calls</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-900/60 text-slate-300">
            <tr>
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">MC Number</th>
              <th className="px-3 py-2">Carrier</th>
              <th className="px-3 py-2">Load ID</th>
              <th className="px-3 py-2">Lane</th>
              <th className="px-3 py-2">Final Offer</th>
              <th className="px-3 py-2">Outcome</th>
              <th className="px-3 py-2">Sentiment</th>
              <th className="px-3 py-2">Summary</th>
            </tr>
          </thead>
          <tbody>
            {calls.map((call) => (
              <tr key={call.id} className="border-t border-slate-800/60">
                <td className="whitespace-nowrap px-3 py-2 text-slate-200">{new Date(call.created_at).toLocaleString()}</td>
                <td className="px-3 py-2 text-slate-300">{call.mc_number || "-"}</td>
                <td className="px-3 py-2 text-slate-300">{call.carrier_name || "-"}</td>
                <td className="px-3 py-2 text-slate-300">{call.load_id || "-"}</td>
                <td className="px-3 py-2 text-slate-300">
                  {call.origin && call.destination ? `${call.origin} -> ${call.destination}` : "-"}
                </td>
                <td className="px-3 py-2 text-slate-100">{currency(call.final_offer)}</td>
                <td className="px-3 py-2">
                  <StatusPill value={call.outcome} variant="outcome" />
                </td>
                <td className="px-3 py-2">
                  <StatusPill value={call.sentiment} variant="sentiment" />
                </td>
                <td className="max-w-xs truncate px-3 py-2 text-slate-400">{call.call_summary || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
