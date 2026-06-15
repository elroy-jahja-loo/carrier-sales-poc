import { KpiCard } from "@/components/kpi-card";
import { OutcomeChart, RateComparisonChart, SentimentChart, VolumeChart } from "@/components/charts";
import { RecentCallsTable } from "@/components/recent-calls-table";
import { getCalls, getSummary } from "@/lib/api";

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function currency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export default async function DashboardPage() {
  const [summary, callsResponse] = await Promise.all([getSummary(), getCalls(25)]);

  const outcomeData = Object.entries(summary.outcomes).map(([name, value]) => ({ name, value }));
  const sentimentData = Object.entries(summary.sentiment).map(([name, value]) => ({ name, value }));

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 md:px-8">
      <section className="mb-8 rounded-3xl border border-slate-700/60 bg-gradient-to-r from-emerald-500/20 via-slate-900/60 to-amber-500/20 p-6 shadow-soft">
        <h1 className="font-display text-3xl font-bold md:text-4xl">Inbound Carrier Sales Automation</h1>
        <p className="mt-2 max-w-3xl text-slate-300">
          Live operating view of automated carrier verification, load matching, negotiation, and booking outcomes.
        </p>
      </section>

      <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <KpiCard label="Total Calls" value={String(summary.total_calls)} />
        <KpiCard label="Booking Rate" value={pct(summary.booking_rate)} />
        <KpiCard label="Booked Loads" value={String(summary.booked_calls)} />
        <KpiCard label="Avg Final Rate" value={currency(summary.average_final_offer)} />
        <KpiCard
          label="Avg Premium vs Loadboard"
          value={`${summary.average_premium_percent.toFixed(1)}%`}
          subtext={`Loadboard avg ${currency(summary.average_loadboard_rate)}`}
        />
        <KpiCard label="Ineligible Carriers" value={String(summary.ineligible_carriers)} />
      </section>

      <section className="mb-8 grid gap-4 lg:grid-cols-2">
        <OutcomeChart data={outcomeData} />
        <SentimentChart data={sentimentData} />
        <VolumeChart data={summary.bookings_over_time} />
        <RateComparisonChart
          loadboard={summary.average_loadboard_rate}
          finalOffer={summary.average_final_offer}
        />
      </section>

      <section className="mb-8">
        <RecentCallsTable calls={callsResponse.calls} />
      </section>

      <section className="glass rounded-2xl p-5 shadow-soft">
        <h2 className="font-display text-xl">HappyRobot Integration Status</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-3">
            <p className="text-sm text-slate-300">MC Verification Tool</p>
            <p className="font-mono text-xs text-emerald-300">/api/carriers/verify</p>
          </div>
          <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-3">
            <p className="text-sm text-slate-300">Load Search Tool</p>
            <p className="font-mono text-xs text-emerald-300">/api/loads/search</p>
          </div>
          <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-3">
            <p className="text-sm text-slate-300">Offer Evaluation Tool</p>
            <p className="font-mono text-xs text-emerald-300">/api/offers/evaluate</p>
          </div>
          <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-3">
            <p className="text-sm text-slate-300">Mock Transfer Tool</p>
            <p className="font-mono text-xs text-emerald-300">/api/transfer/mock</p>
          </div>
          <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-3 md:col-span-2">
            <p className="text-sm text-slate-300">Post-call Webhook</p>
            <p className="font-mono text-xs text-emerald-300">/api/calls/complete</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className="status-pill border border-emerald-500/30 bg-emerald-500/20 text-emerald-300">API secured with X-API-Key</span>
          <span className="status-pill border border-emerald-500/30 bg-emerald-500/20 text-emerald-300">FMCSA verification enabled</span>
          <span className="status-pill border border-emerald-500/30 bg-emerald-500/20 text-emerald-300">Postgres-backed metrics</span>
          <span className="status-pill border border-emerald-500/30 bg-emerald-500/20 text-emerald-300">Dockerized deployment</span>
        </div>
      </section>
    </main>
  );
}
