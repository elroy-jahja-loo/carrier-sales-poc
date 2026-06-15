"use client";

import { useEffect, useState } from "react";
import { CallRecord } from "@/lib/types";
import { StatusPill } from "./status-pill";

function currency(value: number | null): string {
  if (value === null || Number.isNaN(Number(value))) {
    return "-";
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(Number(value));
}

function premium(call: CallRecord): string {
  if (!call.final_offer || !call.loadboard_rate || Number(call.loadboard_rate) <= 0) {
    return "-";
  }
  return `${(((Number(call.final_offer) - Number(call.loadboard_rate)) / Number(call.loadboard_rate)) * 100).toFixed(1)}%`;
}

function dateText(value: string | null): string {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

export function RecentCallsTable({ calls }: { calls: CallRecord[] }) {
  const [selected, setSelected] = useState<CallRecord | null>(null);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSelected(null);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <div className="glass overflow-hidden rounded-2xl shadow-soft">
        <div className="border-b border-slate-700/60 px-4 py-3">
          <h3 className="font-display text-lg">Recent Calls</h3>
          <p className="mt-1 text-xs text-slate-400">Click a row to inspect transcript, pricing, and call metadata.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-slate-900/60 text-slate-300">
              <tr>
                <th className="px-3 py-2">Time</th>
                <th className="px-3 py-2">MC</th>
                <th className="px-3 py-2">Carrier</th>
                <th className="px-3 py-2">Load</th>
                <th className="px-3 py-2">Lane</th>
                <th className="px-3 py-2">Board</th>
                <th className="px-3 py-2">Final</th>
                <th className="px-3 py-2">Premium</th>
                <th className="px-3 py-2">Rounds</th>
                <th className="px-3 py-2">Outcome</th>
                <th className="px-3 py-2">Sentiment</th>
                <th className="px-3 py-2">Summary</th>
              </tr>
            </thead>
            <tbody>
              {calls.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-center text-slate-400" colSpan={12}>No calls have been recorded yet.</td>
                </tr>
              ) : calls.map((call) => (
                <tr
                  key={call.id}
                  className="cursor-pointer border-t border-slate-800/60 transition hover:bg-slate-800/50"
                  onClick={() => setSelected(call)}
                >
                  <td className="whitespace-nowrap px-3 py-2 text-slate-200">{dateText(call.created_at)}</td>
                  <td className="px-3 py-2 text-slate-300">{call.mc_number || "-"}</td>
                  <td className="px-3 py-2 text-slate-300">{call.carrier_name || "-"}</td>
                  <td className="px-3 py-2 text-slate-300">{call.load_id || "-"}</td>
                  <td className="px-3 py-2 text-slate-300">{call.origin && call.destination ? `${call.origin} -> ${call.destination}` : "-"}</td>
                  <td className="px-3 py-2 text-slate-300">{currency(call.loadboard_rate)}</td>
                  <td className="px-3 py-2 text-slate-100">{currency(call.final_offer)}</td>
                  <td className="px-3 py-2 text-slate-300">{premium(call)}</td>
                  <td className="px-3 py-2 text-slate-300">{call.negotiation_rounds ?? "-"}</td>
                  <td className="px-3 py-2"><StatusPill value={call.outcome} variant="outcome" /></td>
                  <td className="px-3 py-2"><StatusPill value={call.sentiment} variant="sentiment" /></td>
                  <td className="max-w-xs px-3 py-2 text-slate-400">
                    <span className="line-clamp-2">{call.call_summary || "-"}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {selected ? <CallDetailModal call={selected} onClose={() => setSelected(null)} /> : null}
    </>
  );
}

function Detail({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-950/40 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 break-words text-sm text-slate-100">{value ?? "-"}</p>
    </div>
  );
}

function CallDetailModal({ call, onClose }: { call: CallRecord; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-3xl border border-slate-700 bg-slate-900 p-5 shadow-2xl"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h3 className="font-display text-2xl font-bold text-slate-100">Call Detail #{call.id}</h3>
            <p className="mt-1 text-sm text-slate-400">{call.origin && call.destination ? `${call.origin} -> ${call.destination}` : "No lane captured"}</p>
          </div>
          <button className="rounded-full border border-slate-600 px-3 py-1 text-sm text-slate-200 hover:bg-slate-800" onClick={onClose}>Close</button>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          <StatusPill value={call.outcome} variant="outcome" />
          <StatusPill value={call.sentiment} variant="sentiment" />
          {call.transfer_successful !== null ? (
            <span className="status-pill border border-sky-500/30 bg-sky-500/20 text-sky-300">
              transfer {call.transfer_successful ? "successful" : "not completed"}
            </span>
          ) : null}
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <Detail label="Time" value={dateText(call.created_at)} />
          <Detail label="HappyRobot Run" value={call.happyrobot_run_id} />
          <Detail label="Session" value={call.session_id} />
          <Detail label="MC Number" value={call.mc_number} />
          <Detail label="Carrier" value={call.carrier_name} />
          <Detail label="Load ID" value={call.load_id} />
          <Detail label="Origin" value={call.origin} />
          <Detail label="Destination" value={call.destination} />
          <Detail label="Equipment" value={call.equipment_type} />
          <Detail label="Pickup" value={dateText(call.pickup_datetime)} />
          <Detail label="Delivery" value={dateText(call.delivery_datetime)} />
          <Detail label="Commodity" value={call.commodity_type} />
          <Detail label="Weight" value={call.weight ? `${call.weight.toLocaleString()} lb` : null} />
          <Detail label="Miles" value={call.miles} />
          <Detail label="Pieces" value={call.num_of_pieces} />
          <Detail label="Dimensions" value={call.dimensions} />
          <Detail label="Loadboard" value={currency(call.loadboard_rate)} />
          <Detail label="Final / Accepted Offer" value={currency(call.final_offer)} />
          <Detail label="Premium" value={premium(call)} />
          <Detail label="Negotiation Rounds" value={call.negotiation_rounds} />
          <Detail label="Duration" value={call.call_duration_seconds ? `${call.call_duration_seconds}s` : null} />
          <Detail label="Failure Reason" value={call.failure_reason} />
        </div>

        <div className="mt-4 rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Full Summary</p>
          <p className="mt-2 whitespace-pre-wrap text-sm text-slate-100">{call.call_summary || "No summary captured."}</p>
        </div>

        <div className="mt-4 rounded-2xl border border-slate-700/60 bg-slate-950/40 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Transcript</p>
          <div className="mt-2 max-h-64 overflow-y-auto whitespace-pre-wrap text-sm text-slate-300">
            {call.transcript || "No transcript captured."}
          </div>
        </div>
      </div>
    </div>
  );
}
