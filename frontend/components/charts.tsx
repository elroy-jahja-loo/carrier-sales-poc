"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#10b981", "#f59e0b", "#ef4444", "#64748b", "#06b6d4", "#f97316"];

export function OutcomeChart({ data }: { data: Array<{ name: string; value: number }> }) {
  return (
    <div className="glass rounded-2xl p-4 shadow-soft">
      <h3 className="mb-3 font-display text-lg">Outcome Distribution</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" outerRadius={100} innerRadius={55}>
              {data.map((_, i) => (
                <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function SentimentChart({ data }: { data: Array<{ name: string; value: number }> }) {
  return (
    <div className="glass rounded-2xl p-4 shadow-soft">
      <h3 className="mb-3 font-display text-lg">Sentiment Distribution</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function VolumeChart({ data }: { data: Array<{ date: string; calls: number }> }) {
  return (
    <div className="glass rounded-2xl p-4 shadow-soft">
      <h3 className="mb-3 font-display text-lg">Recent Call Volume</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="date" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" allowDecimals={false} />
            <Tooltip />
            <Line type="monotone" dataKey="calls" stroke="#f59e0b" strokeWidth={3} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function RateComparisonChart({
  loadboard,
  finalOffer,
}: {
  loadboard: number;
  finalOffer: number;
}) {
  const data = [
    { name: "Loadboard", value: loadboard },
    { name: "Final Offer", value: finalOffer },
  ];
  return (
    <div className="glass rounded-2xl p-4 shadow-soft">
      <h3 className="mb-3 font-display text-lg">Average Final Offer vs Loadboard</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {data.map((_, i) => (
                <Cell key={`rate-cell-${i}`} fill={i === 0 ? "#06b6d4" : "#10b981"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
