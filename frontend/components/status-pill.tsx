type Variant = "outcome" | "sentiment";

const outcomeClasses: Record<string, string> = {
  booked: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
  declined: "bg-rose-500/20 text-rose-300 border border-rose-500/30",
  ineligible: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
  transferred: "bg-sky-500/20 text-sky-300 border border-sky-500/30",
  no_load_found: "bg-slate-500/20 text-slate-300 border border-slate-500/30",
  unresolved: "bg-orange-500/20 text-orange-300 border border-orange-500/30",
  unknown: "bg-zinc-500/20 text-zinc-300 border border-zinc-500/30",
};

const sentimentClasses: Record<string, string> = {
  positive: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30",
  neutral: "bg-amber-500/20 text-amber-300 border border-amber-500/30",
  negative: "bg-rose-500/20 text-rose-300 border border-rose-500/30",
  unknown: "bg-zinc-500/20 text-zinc-300 border border-zinc-500/30",
};

export function StatusPill({ value, variant }: { value: string; variant: Variant }) {
  const base = "status-pill";
  const classes = variant === "outcome" ? outcomeClasses[value] || outcomeClasses.unknown : sentimentClasses[value] || sentimentClasses.unknown;
  return <span className={`${base} ${classes}`}>{value.replaceAll("_", " ")}</span>;
}
